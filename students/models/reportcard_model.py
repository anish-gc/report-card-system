from django.db import models

from students.managers.report_card_manager import ReportCardManager
from students.models.student_model import Student
from utilities.base_model import BaseModel
from django.db.models import Avg, Sum, Count, Q
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal




class ReportCard(BaseModel):
    """
    ReportCard model representing a student's performance for a term.
    Optimized for efficient querying and aggregation.
    """

    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
        ("Final", "Final Term"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="report_cards",
        db_index=True,
        help_text="Student this report card belongs to",
    )
    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES,
        db_index=True,
        help_text="Academic term (e.g., Term 1, Term 2)",
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        db_index=True,
        help_text="Academic year",
    )

    total_subjects = models.PositiveIntegerField(
        default=0, help_text="Total number of subjects"
    )
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Average score across all subjects",
    )
    total_score = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total score across all subjects",
    )

    # Additional metadata
    generated_at = models.DateTimeField(
        auto_now_add=True, help_text="When the report card was generated"
    )
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the report card is published to students",
    )

    objects = ReportCardManager()

    class Meta:
        db_table = "report_cards"
        verbose_name = "Report Card"
        verbose_name_plural = "Report Cards"
        ordering = ["-year", "-term", "student__name"]
        unique_together = ["student", "term", "year"]
        indexes = [
            models.Index(fields=["student", "year"]),
            models.Index(fields=["year", "term"]),
            models.Index(fields=["student", "year", "term"]),
            models.Index(fields=["year", "is_published"]),
        ]

    # def clean(self):
    #     """Custom validation"""
    #     super().clean()
    #     current_year = timezone.now().year
    #     if self.year > current_year + 1:
    #         raise ValidationError(
    #             {"year": "Year cannot be more than one year in the future"}
    #         )

    # def __str__(self):
    #     return f"{self.student.name} - {self.term} {self.year}"

    # def calculate_aggregated_data(self):
    #     """Calculate and update aggregated data"""
    #     marks_data = self.marks.aggregate(
    #         total_subjects=Count("id"),
    #         average_score=Avg("score"),
    #         total_score=Sum("score"),
    #     )

    #     self.total_subjects = marks_data["total_subjects"] or 0
    #     self.average_score = marks_data["average_score"] or Decimal("0.00")
    #     self.total_score = marks_data["total_score"] or Decimal("0.00")

    # def save(self, *args, **kwargs):
    #     """Override save to calculate aggregated data"""
    #     super().save(*args, **kwargs)
    #     # Recalculate aggregated data after saving
    #     self.calculate_aggregated_data()
    #     if kwargs.get("update_fields"):
    #         # If specific fields were updated, add our calculated fields
    #         kwargs["update_fields"] = list(kwargs["update_fields"]) + [
    #             "total_subjects",
    #             "average_score",
    #             "total_score",
    #         ]
    #     super().save(update_fields=["total_subjects", "average_score", "total_score"])









# # Custom QuerySets for advanced filtering
# class OptimizedQuerySet(models.QuerySet):
#     """Base queryset with common optimizations"""
    
#     def active(self):
#         """Filter for active records"""
#         return self.filter(is_active=True)
    
#     def for_year(self, year):
#         """Filter for specific year"""
#         return self.filter(year=year)


# # Performance monitoring and caching utilities
# from django.core.cache import cache
# from django.db.models import Prefetch

# class ReportCardQuerySet(OptimizedQuerySet):
#     """Optimized queryset for ReportCard with caching"""
    
#     def with_complete_data(self):
#         """Fetch report cards with all related data in optimized way"""
#         return self.select_related('student').prefetch_related(
#             Prefetch(
#                 'marks',
#                 queryset=Mark.objects.select_related('subject').order_by('subject__code')
#             )
#         )
    
#     def student_year_summary(self, student_id, year):
#         """Get cached summary for student year"""
#         cache_key = f"report_summary_{student_id}_{year}"
#         summary = cache.get(cache_key)
        
#         if summary is None:
#             summary = self.filter(
#                 student_id=student_id, 
#                 year=year
#             ).aggregate(
#                 avg_score=Avg('marks__score'),
#                 total_subjects=Count('marks'),
#                 total_marks=Sum('marks__score')
#             )
#             cache.set(cache_key, summary, 3600)  # Cache for 1 hour
        
#         return summary


# # Apply custom QuerySet to models
# ReportCard.objects = ReportCardQuerySet.as_manager()