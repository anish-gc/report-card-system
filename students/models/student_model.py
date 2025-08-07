from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Avg, Sum, Count, Q
from utilities.base_model import BaseModel
from django.utils import timezone


class Student(BaseModel):
    """
    Student model with optimized fields and proper validation.
    Using UUID for better security and scalability.
    """

    name = models.CharField(
        max_length=100,
        db_index=True,  # Index for search performance
        help_text="Full name of the student",
    )
    email = models.EmailField(
        unique=True,
        db_index=True,  # Index for lookup performance
        help_text="Unique email address",
    )
    date_of_birth = models.DateField(help_text="Student's date of birth")

    student_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9]{6,20}$",
                message="Student ID must be 6-20 characters, alphanumeric uppercase only",
            )
        ],
        help_text="Unique student identification number",
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether the student is currently active"
    )

    class Meta:
        db_table = "students"
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "is_active"]),
            models.Index(fields=["email", "is_active"]),
        ]
    

  
    def __str__(self):
        return f"{self.name} ({self.student_id})"

    # def get_current_report_cards(self, year=None):
    #     """Get report cards for current or specified year"""
    #     year = year or timezone.now().year
    #     return self.report_cards.filter(year=year).select_related().prefetch_related('marks__subject')

    # def get_overall_average(self, year=None):
    #     """Calculate overall average for a year with database aggregation"""
    #     year = year or timezone.now().year
    #     result = self.report_cards.filter(year=year).aggregate(
    #         avg_score=Avg('marks__score')
    #     )
    #     return result['avg_score'] or Decimal('0.00')
