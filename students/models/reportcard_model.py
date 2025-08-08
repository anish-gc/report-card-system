from django.db import models

from students.managers.report_card_manager import ReportCardManager
from students.models.student_model import Student
from utilities.base_model import BaseModel
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
        ]


    def __str__(self):
        return f"{self.student.name} - {self.term} {self.year}"







