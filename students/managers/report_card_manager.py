from django.db import models
from django.db.models import Avg, Sum, Count, F, Prefetch, Q,  Max, Min
from decimal import Decimal
from typing import Dict, List, Any, Optional


class ReportCardQuerySet(models.QuerySet):
    """Custom QuerySet for ReportCard with optimized queries."""

    def with_marks(self):
        """Prefetch related marks and subjects for efficient queries."""
        from students.models import Mark  # Import here to avoid circular imports

        return self.prefetch_related(
            Prefetch("marks", queryset=Mark.objects.select_related("subject"))
        )

    def with_student_details(self):
        """Select related student information."""
        return self.select_related("student")

    def for_year(self, year: int):
        """Filter report cards by academic year."""
        return self.filter(year=year)

    def for_term(self, term: str):
        """Filter report cards by term."""
        return self.filter(term=term)

    def with_aggregated_data(self):
        """Annotate with aggregated mark data."""
        return self.annotate(
            calculated_average=Avg("marks__score"),
            calculated_total=Sum("marks__score"),
            subject_count=Count("marks"),
            highest_score=models.Max("marks__score"),
            lowest_score=models.Min("marks__score"),
        )

    def for_student_year(self, student_id: int, year: int):
        """Get all report cards for a student in a specific year."""
        return self.filter(student_id=student_id, year=year)


class ReportCardManager(models.Manager):
    """Enhanced manager for ReportCard model."""

    def get_student_report_cards_optimized(self, student_id, year):
        """
        Get student report cards with all calculations done in database.
        This eliminates the need for separate calculated fields.
        """
        return (
            self.select_related("student")
            .prefetch_related("marks__subject")
            .filter(student_id=student_id, year=year, is_active=True)
            .annotate(
                subject_count=Count("marks"),
                calculated_average=Avg("marks__score"),
                calculated_total=Sum("marks__score"),
                highest_score=Max("marks__score"),
                lowest_score=Min("marks__score"),
            )
            .order_by("term")
        )

    def get_queryset(self):
        return ReportCardQuerySet(self.model, using=self._db)

    def with_marks(self):
        return self.get_queryset().with_marks()

    def with_student_details(self):
        return self.get_queryset().with_student_details()

    def for_year(self, year: int):
        return self.get_queryset().for_year(year)

    def for_term(self, term: str):
        return self.get_queryset().for_term(term)

    def get_student_report_cards(self, student_id: int, year: int) -> models.QuerySet:
        """
        Get all report cards for a student in a given year with aggregated data.
        Optimized for performance with proper prefetching.
        """
        return (
            self.get_queryset()
            .for_student_year(student_id, year)
            .with_marks()
            .with_aggregated_data()
            .order_by("term")
        )

    def get_detailed_report_card(self, report_card_id: str):
        """Get a single report card with all related data."""
        return (
            self.get_queryset()
            .with_marks()
            .with_student_details()
            .with_aggregated_data()
            .get(id=report_card_id)
        )

    def calculate_year_averages(self, student_id: str, year: int) -> Dict[str, Any]:
        """
        Calculate average scores per subject and overall average for a year.
        Performs aggregation in the database for efficiency.
        """
        from students.models import Mark, Subject

        # Get all marks for the student in the given year
        marks_qs = (
            Mark.objects.filter(
                report_card__student_id=student_id, report_card__year=year
            )
            .select_related("subject", "report_card")
            .values("subject__code", "subject__name")
            .annotate(
                average_score=Avg("score"),
                term_count=Count("report_card__term", distinct=True),
            )
            .order_by("subject__code")
        )

        # Calculate overall average
        overall_avg = Mark.objects.filter(
            report_card__student_id=student_id, report_card__year=year
        ).aggregate(overall_average=Avg("score"))
        return {
            "subject_averages": list(marks_qs),
            "overall_average": overall_avg["overall_average"] or Decimal("0.00"),
            "year": year,
            "studentreferenceId": student_id,
        }
