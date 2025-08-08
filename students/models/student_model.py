from django.db import models

from utilities.base_model import BaseModel


class Student(BaseModel):
    """
    Student model with optimized fields and proper validation.
    Using id for better security and scalability.
    """

    name = models.CharField(
        max_length=100,
        db_index=True, 
        help_text="Full name of the student",
    )
    email = models.EmailField(
        unique=True,
        db_index=True,  
        help_text="Unique email address",
    )
    date_of_birth = models.DateField(help_text="Student's date of birth")

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
        return f"{self.name} ({self.email})"
