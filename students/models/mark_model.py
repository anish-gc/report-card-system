from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Avg

from students.managers.mark_manager import MarkManager
from students.models.reportcard_model import ReportCard
from students.models.subject_model import Subject
from utilities.base_model import BaseModel




class Mark(BaseModel):
    """
    Mark model representing individual subject marks.
    Optimized for aggregation queries and reporting.
    """

    report_card = models.ForeignKey(
        "students.ReportCard",
        on_delete=models.CASCADE,
        related_name="marks",
        db_index=True,
        help_text="Report card this mark belongs to",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="marks",
        db_index=True,
        help_text="Subject for this mark",
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Score out of 100",
    )

  
    remarks = models.TextField(
        blank=True, help_text="Teacher's remarks for this subject"
    )

    objects = MarkManager()

    class Meta:
        db_table = "marks"
        verbose_name = "Mark"
        verbose_name_plural = "Marks"
        ordering = ["report_card", "subject__code"]
        unique_together = ["report_card", "subject"]
        indexes = [
            models.Index(fields=["report_card", "subject"]),
            models.Index(fields=["subject", "score"]),
            models.Index(fields=["report_card", "score"]),
    
        ]

    def clean(self):
        """Custom validation"""
        super().clean()
        if self.report_card and self.subject:
            # Ensure subject is active
            if not self.subject.is_active:
                raise ValidationError(
                    {"subject": "Cannot assign marks to inactive subjects"}
                )

    def __str__(self):
        return f"{self.report_card.student.name} - {self.subject.code}: {self.score}"

    def save(self, *args, **kwargs):
        """Override save to calculate grade and update report card aggregates"""
      

        super().save(*args, **kwargs)

        # Update report card aggregated data
        # self.report_card.calculate_aggregated_data()
        # self.report_card.save(
        #     update_fields=["total_subjects", "average_score", "total_score"]
        # )

    @property
    def percentage(self):
        """Return score as percentage"""
        if self.score:
            return float(self.score)
        else:
            return 0

    @property
    def is_passing(self):
        """Check if the mark is passing (>= 50)"""
        if self.score:
            return self.score >= 50
        return False
