from django.db import models
from django.db.models import Avg, Sum, Count, F
from decimal import Decimal
from typing import Dict, List, Any

class MarkQuerySet(models.QuerySet):
    """Custom QuerySet for Mark with optimized queries."""
    
    def with_report_card_details(self):
        """Select related report card and student information."""
        return self.select_related('report_card__student', 'report_card')
    
    def with_subject_details(self):
        """Select related subject information."""
        return self.select_related('subject')
    
    def for_student(self, student_id: int):
        """Filter marks by student."""
        return self.filter(report_card__student_id=student_id)
    
    def for_subject(self, subject_id: int):
        """Filter marks by subject."""
        return self.filter(subject_id=subject_id)
    
    def for_year(self, year: int):
        """Filter marks by academic year."""
        return self.filter(report_card__year=year)
    
    def for_term(self, term: str):
        """Filter marks by term."""
        return self.filter(report_card__term=term)
    
    def above_score(self, score: float):
        """Filter marks above a certain score."""
        return self.filter(score__gte=score)
    
    def below_score(self, score: float):
        """Filter marks below a certain score."""
        return self.filter(score__lte=score)



class MarkManager(models.Manager):
    """Enhanced manager for Mark model."""
    
    def get_queryset(self):
        return MarkQuerySet(self.model, using=self._db)
    
    def with_report_card_details(self):
        return self.get_queryset().with_report_card_details()
    
    def with_subject_details(self):
        return self.get_queryset().with_subject_details()
    
    def for_student(self, student_id: int):
        return self.get_queryset().for_student(student_id)
    
    def for_subject(self, subject_id: int):
        return self.get_queryset().for_subject(subject_id)
    
    def for_year(self, year: int):
        return self.get_queryset().for_year(year)
    
    def for_term(self, term: str):
        return self.get_queryset().for_term(term)
    
    def get_subject_performance(self, subject_id: int, year: int = None) -> Dict[str, Any]:
        """
        Get performance statistics for a subject across all students.
        """
        queryset = self.for_subject(subject_id)
        if year:
            queryset = queryset.for_year(year)
        
        stats = queryset.aggregate(
            average_score=Avg('score'),
            highest_score=models.Max('score'),
            lowest_score=models.Min('score'),
            total_students=Count('report_card__student', distinct=True),
            total_marks=Count('id')
        )
        
        return {
            'subject_id': subject_id,
            'year': year,
            **stats
        }
    
    def get_student_subject_progress(self, student_id: int, subject_id: int, year: int) -> List[Dict]:
        """
        Get a student's progress in a specific subject across terms in a year.
        """
        marks = (
            self.for_student(student_id)
            .for_subject(subject_id)
            .for_year(year)
            .select_related('report_card')
            .values('report_card__term', 'score', 'remarks')
            .order_by('report_card__term')
        )
        
        return list(marks)
    
    def bulk_create_marks(self, report_card, marks_data: List[Dict]) -> List:
        """
        Bulk create marks for a report card.
        Efficiently handles multiple marks creation.
        """
        mark_objects = []
        for mark_data in marks_data:
            mark_objects.append(
                self.model(
                    report_card=report_card,
                    subject_id=mark_data['subject_id'],
                    score=mark_data['score'],
                    remarks=mark_data.get('remarks', '')
                )
            )
        
        return self.bulk_create(mark_objects)
    
    def update_report_card_aggregates(self, report_card):
        """
        Update the aggregated fields in the report card based on marks.
        Should be called after marks are added/updated/deleted.
        """
        marks_stats = (
            self.filter(report_card=report_card)
            .aggregate(
                total_score=Sum('score'),
                average_score=Avg('score'),
                total_subjects=Count('id')
            )
        )
        
        # Update the report card
        report_card.total_score = marks_stats['total_score'] or Decimal('0.00')
        report_card.average_score = marks_stats['average_score'] or Decimal('0.00')
        report_card.total_subjects = marks_stats['total_subjects'] or 0
        report_card.save(update_fields=['total_score', 'average_score', 'total_subjects'])
        
        return report_card