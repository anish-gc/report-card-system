from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.db import transaction, models
from django.core.cache import cache

from decimal import Decimal
from typing import Dict, List, Optional
import logging
from django.utils import timezone
from .models import ReportCard, Mark, Student

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_report_card_aggregates(self, report_card_id: str):
    """
    Calculate and update aggregated fields for a report card.
    This includes total_score, average_score, and total_subjects.
    """
    try:
        with transaction.atomic():
            report_card = ReportCard.objects.select_for_update().get(id=report_card_id)

            # Calculate aggregates from marks
            marks_stats = Mark.objects.filter(
                report_card=report_card, is_active=True
            ).aggregate(
                total_score=models.Sum("score"),
                average_score=models.Avg("score"),
                total_subjects=models.Count("id"),
            )

            # Update report card with calculated values
            report_card.total_score = marks_stats["total_score"] or Decimal("0.00")
            report_card.average_score = marks_stats["average_score"] or Decimal("0.00")
            report_card.total_subjects = marks_stats["total_subjects"] or 0

            # Calculate grade based on average
            report_card.grade = calculate_grade_from_average(report_card.average_score)
            report_card.percentage = calculate_percentage(report_card.average_score)
            report_card.calculation_status = "completed"
            report_card.last_calculated = timezone.now()  # Add this line
            print('randi ko ban')
            report_card.save(
                update_fields=[
                    "total_score",
                    "average_score",
                    "total_subjects",
                    "grade",
                    "percentage",
                    "calculation_status",
                    "last_calculated",  # Add this
                ]
            )

            # Clear related cache
            cache_key = f"report_card_{report_card_id}_stats"
            cache.delete(cache_key)

            logger.info(
                f"Successfully calculated aggregates for report card {report_card_id}"
            )

            return {
                "report_card_id": report_card_id,
                "total_score": float(report_card.total_score),
                "average_score": float(report_card.average_score),
                "total_subjects": report_card.total_subjects,
                "grade": report_card.grade,
                "percentage": float(report_card.percentage),
            }

    except ReportCard.DoesNotExist:
        logger.error(f"Report card {report_card_id} not found")
        raise self.retry(countdown=60, max_retries=3)

    except Exception as exc:
        logger.error(
            f"Error calculating aggregates for report card {report_card_id}: {exc}"
        )
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=3)
def calculate_student_grade(self, student_id: str, year: int):
    """
    Calculate overall grade and performance metrics for a student in a given year.
    """
    try:
        student = Student.objects.get(id=student_id, is_active=True)

        # Get all report cards for the student in the given year
        report_cards = ReportCard.objects.filter(
            student=student, year=year, is_active=True
        ).prefetch_related("marks")

        if not report_cards.exists():
            return {
                "error": f"No report cards found for student {student_id} in year {year}"
            }

        # Calculate yearly averages
        yearly_stats = {
            "student_id": student_id,
            "year": year,
            "term_averages": [],
            "subject_averages": {},
            "overall_average": Decimal("0.00"),
            "overall_grade": "",
            "total_subjects": 0,
            "terms_completed": 0,
        }

        total_average = Decimal("0.00")
        terms_count = 0
        all_subjects = set()

        for report_card in report_cards:
            if report_card.average_score > 0:
                yearly_stats["term_averages"].append(
                    {
                        "term": report_card.term,
                        "average": float(report_card.average_score),
                        "grade": report_card.grade
                        or calculate_grade_from_average(report_card.average_score),
                    }
                )
                total_average += report_card.average_score
                terms_count += 1

                # Track subjects
                for mark in report_card.marks.all():
                    subject_key = mark.subject.code
                    all_subjects.add(subject_key)

                    if subject_key not in yearly_stats["subject_averages"]:
                        yearly_stats["subject_averages"][subject_key] = {
                            "subject_name": mark.subject.name,
                            "scores": [],
                            "average": Decimal("0.00"),
                        }

                    yearly_stats["subject_averages"][subject_key]["scores"].append(
                        float(mark.score)
                    )

        # Calculate overall statistics
        if terms_count > 0:
            yearly_stats["overall_average"] = float(total_average / terms_count)
            yearly_stats["overall_grade"] = calculate_grade_from_average(
                total_average / terms_count
            )

        yearly_stats["terms_completed"] = terms_count
        yearly_stats["total_subjects"] = len(all_subjects)

        # Calculate subject averages
        for subject_code, subject_data in yearly_stats["subject_averages"].items():
            scores = subject_data["scores"]
            if scores:
                subject_data["average"] = sum(scores) / len(scores)
                subject_data["grade"] = calculate_grade_from_average(
                    subject_data["average"]
                )

        # Cache the results
        cache_key = f"student_{student_id}_year_{year}_performance"
        cache.set(cache_key, yearly_stats, timeout=3600)  # Cache for 1 hour

        logger.info(
            f"Successfully calculated yearly performance for student {student_id}, year {year}"
        )
        return yearly_stats

    except Student.DoesNotExist:
        logger.error(f"Student {student_id} not found")
        return {"error": f"Student {student_id} not found"}

    except Exception as exc:
        logger.error(f"Error calculating student grade: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=2)
def calculate_class_averages(self, year: int, term: str = None):
    """
    Calculate class-wide averages and statistics for a given year and optionally term.
    """
    try:
        queryset = ReportCard.objects.filter(year=year, is_active=True)

        if term:
            queryset = queryset.filter(term=term)

        queryset = queryset.prefetch_related("marks__subject", "student")

        if not queryset.exists():
            return {
                "error": f"No report cards found for year {year}"
                + (f" term {term}" if term else "")
            }

        class_stats = {
            "year": year,
            "term": term,
            "total_students": 0,
            "class_average": 0.0,
            "subject_averages": {},
            "grade_distribution": {
                "A+": 0,
                "A": 0,
                "B+": 0,
                "B": 0,
                "C+": 0,
                "C": 0,
                "D": 0,
                "F": 0,
            },
            "performance_metrics": {
                "highest_average": 0.0,
                "lowest_average": 0.0,
                "students_above_75": 0,
                "students_below_50": 0,
            },
        }

        total_class_average = Decimal("0.00")
        student_count = 0
        highest_avg = Decimal("0.00")
        lowest_avg = Decimal("100.00")

        # Process each report card
        for report_card in queryset:
            student_count += 1
            avg_score = report_card.average_score or Decimal("0.00")

            # Update class totals
            total_class_average += avg_score

            # Track highest and lowest
            if avg_score > highest_avg:
                highest_avg = avg_score
            if avg_score < lowest_avg:
                lowest_avg = avg_score

            # Grade distribution
            grade = report_card.grade or calculate_grade_from_average(avg_score)
            if grade in class_stats["grade_distribution"]:
                class_stats["grade_distribution"][grade] += 1

            # Performance metrics
            if avg_score >= 75:
                class_stats["performance_metrics"]["students_above_75"] += 1
            if avg_score < 50:
                class_stats["performance_metrics"]["students_below_50"] += 1

            # Subject-wise averages
            for mark in report_card.marks.all():
                subject_code = mark.subject.code
                if subject_code not in class_stats["subject_averages"]:
                    class_stats["subject_averages"][subject_code] = {
                        "subject_name": mark.subject.name,
                        "total_score": Decimal("0.00"),
                        "student_count": 0,
                        "average": 0.0,
                    }

                class_stats["subject_averages"][subject_code][
                    "total_score"
                ] += mark.score
                class_stats["subject_averages"][subject_code]["student_count"] += 1

        # Calculate final averages
        if student_count > 0:
            class_stats["class_average"] = float(total_class_average / student_count)
            class_stats["total_students"] = student_count
            class_stats["performance_metrics"]["highest_average"] = float(highest_avg)
            class_stats["performance_metrics"]["lowest_average"] = float(lowest_avg)

        # Calculate subject averages
        for subject_code, subject_data in class_stats["subject_averages"].items():
            if subject_data["student_count"] > 0:
                subject_data["average"] = float(
                    subject_data["total_score"] / subject_data["student_count"]
                )
            del subject_data["total_score"]  # Remove temporary field

        # Cache results
        cache_key = f"class_stats_{year}"
        if term:
            cache_key += f"_{term}"
        cache.set(cache_key, class_stats, timeout=1800)  # Cache for 30 minutes

        logger.info(
            f"Successfully calculated class averages for year {year}"
            + (f" term {term}" if term else "")
        )
        return class_stats

    except Exception as exc:
        logger.error(f"Error calculating class averages: {exc}")
        raise self.retry(exc=exc, countdown=120, max_retries=2)


@shared_task(bind=True, max_retries=2)
def bulk_calculate_report_cards(self, report_card_ids: List[str]):
    """
    Bulk calculate aggregates for multiple report cards.
    Useful for batch operations and data migrations.
    """
    try:
        results = []
        failed_calculations = []

        for report_card_id in report_card_ids:
            try:
                result = calculate_report_card_aggregates.apply_async(
                    args=[report_card_id], queue="calculations"
                )
                results.append(
                    {
                        "report_card_id": report_card_id,
                        "task_id": result.id,
                        "status": "queued",
                    }
                )
            except Exception as e:
                failed_calculations.append(
                    {"report_card_id": report_card_id, "error": str(e)}
                )

        logger.info(f"Bulk calculation initiated for {len(results)} report cards")

        return {
            "total_queued": len(results),
            "failed_count": len(failed_calculations),
            "results": results,
            "failures": failed_calculations,
        }

    except Exception as exc:
        logger.error(f"Error in bulk calculation: {exc}")
        raise self.retry(exc=exc, countdown=120, max_retries=2)


@shared_task
def cleanup_old_cache():
    """
    Periodic task to clean up old cached calculation results.
    """
    try:
        # This is a placeholder - implement based on your cache backend
        # For Redis, you might use pattern matching to delete old keys
        logger.info("Cache cleanup completed")
        return {"status": "completed"}
    except Exception as exc:
        logger.error(f"Error during cache cleanup: {exc}")
        return {"status": "failed", "error": str(exc)}


# Helper functions
def calculate_grade_from_average(average_score):
    """Calculate letter grade based on average score."""
    if average_score >= 95:
        return "A+"
    elif average_score >= 90:
        return "A"
    elif average_score >= 85:
        return "B+"
    elif average_score >= 80:
        return "B"
    elif average_score >= 75:
        return "C+"
    elif average_score >= 70:
        return "C"
    elif average_score >= 60:
        return "D"
    else:
        return "F"


def calculate_percentage(average_score):
    """Calculate percentage from average score."""
    return average_score  # Assuming average is already out of 100
