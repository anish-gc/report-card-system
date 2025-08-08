from django.db import models
from django.core.validators import RegexValidator
from utilities.base_model import BaseModel


class Subject(BaseModel):
    """
    Subject model with proper validation and optimization.
    """

    name = models.CharField(max_length=100, db_index=True, help_text="Subject name")
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{2,4}[0-9]{2,4}$",
                message="Subject code must be in format: 2-4 letters followed by 2-4 numbers (e.g., MATH101)",
            )
        ],
        help_text="Unique subject code (e.g., MATH101, ENG201)",
    )

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['name', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
   