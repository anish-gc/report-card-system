from students.models.mark_model import Mark
from students.models.reportcard_model import ReportCard
from students.models.student_model import Student
from students.serializers.mark_serializer import (
    MarkSummarySerializer,
    MarkWriteSerializer,
)
from utilities import global_parameters
from utilities.base_serializer import ReadBaseSerializer, WriteBaseSerializer
from rest_framework import serializers
from django.db import transaction

from utilities.custom_exception_class import CustomAPIException
from utilities.global_functions import model_validation, validate_unique_fields


class ReportCardWriteSerializer(WriteBaseSerializer):
    """Optimized serializer for creating/updating report cards."""

    student = serializers.IntegerField(
        error_messages={
            "required": "Student is required to create reportcard.",
            "does_not_exist": "Student does not exist or is inactive.",
        },
    )

    term = serializers.ChoiceField(
        choices=ReportCard.TERM_CHOICES,
        error_messages={
            "required": "Term is required.",
            "invalid_choice": "Invalid term choice.Please choose Term 1, Term 2, Term 3 or Final",
        },
    )

    year = serializers.IntegerField(
        min_value=2025,
        max_value=2100,
        error_messages={
            "required": "Year is required.",
            "min_value": "Year cannot be less than 2025.",
            "max_value": "Year cannot be greater than 2100.",
        },
    )

    marks = MarkWriteSerializer(many=True, required=False)

    def validate(self, data):
        student_reference_id = data.get("student")
        student = model_validation(Student, 'Please provide the correct student to create reportcard', {"id":student_reference_id})
        term = data.get("term")
        year = data.get("year")

        # Build the query for existing records
        existing_query = ReportCard.objects.filter(
            student=student, term=term, year=year, is_active=True
        )

        # If updating, exclude the current instance
        if self.instance:
            existing_query = existing_query.exclude(pk=self.instance.pk)
        if existing_query.exists():
            raise CustomAPIException(
                f"Report card for student {student}, for {term}, and year {year} already exists."
            )
        return data | {"student": student}
       

    @transaction.atomic
    def create(self, validated_data):
        marks_data = validated_data.pop("marks", [])

        # Create report card
        report_card = ReportCard.objects.create(**validated_data)

        # Create marks if provided
        if marks_data:
            mark_objects = []
            for mark_data in marks_data:
                mark_objects.append(
                    Mark(
                        report_card=report_card,
                        subject=mark_data["subject"],
                        score=mark_data["score"],
                        remarks=mark_data.get("remarks", ""),
                    )
                )

            Mark.objects.bulk_create(mark_objects)
            # Update aggregated fields
            Mark.objects.update_report_card_aggregates(report_card)

        return report_card

    @transaction.atomic
    def update(self, instance, validated_data):
        marks_data = validated_data.pop("marks", None)
        # Update report card fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle marks update if provided
        if marks_data is not None:
            # Delete existing marks and create new ones
            # This is simpler than trying to match existing marks

            instance.marks.all().delete()

            mark_objects = []
            for mark_data in marks_data:
                mark_objects.append(
                    Mark(
                        report_card=instance,
                        subject=mark_data["subject"],
                        score=mark_data["score"],
                        remarks=mark_data.get("remarks", ""),
                    )
                )
            if mark_objects:
                Mark.objects.bulk_create(mark_objects)

            # Update aggregated fields
            Mark.objects.update_report_card_aggregates(instance)

        return instance


class ReportCardReadSerializer(serializers.Serializer):
    """Optimized read serializer for report cards with all details."""
    reportCardreferenceId = serializers.CharField(source="id", read_only=True)

    studentReferenceId = serializers.CharField(source="student.id", read_only=True)
    studentName = serializers.CharField(source="student.name", read_only=True)
    term = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True)

    # Use calculated fields from database annotations (preferred approach)
    totalSubjects = serializers.SerializerMethodField()
    averageScore = serializers.SerializerMethodField()
    totalScore = serializers.SerializerMethodField()
    highestScore = serializers.SerializerMethodField()
    lowestScore = serializers.SerializerMethodField()
    
    # New fields for grade and percentage
    grade = serializers.CharField(read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Calculation status fields
    calculationStatus = serializers.CharField(source="calculation_status", read_only=True)
    lastCalculated = serializers.DateTimeField(source="last_calculated", read_only=True)

    marks = MarkSummarySerializer(many=True, read_only=True)

    def get_totalSubjects(self, obj):
        """Get total subjects count."""
        if hasattr(obj, "subject_count"):
            return obj.subject_count
        return getattr(
            obj, "total_subjects", obj.marks.count() if obj.marks.exists() else 0
        )

    def get_averageScore(self, obj):
        """Get average score with proper decimal formatting."""
        if hasattr(obj, "average_score"):
            return f"{obj.average_score:.2f}"
        else:
            # Fallback calculation if needed
            marks = obj.marks.all()
            if marks:
                total = sum(float(mark.score) for mark in marks)
                return f"{total / len(marks):.2f}"
            return "0.00"

    def get_totalScore(self, obj):
        """Get total score with proper decimal formatting."""
        if hasattr(obj, "total_score"):
            return f"{obj.total_score:.2f}"
        else:
            # Fallback calculation if needed
            marks = obj.marks.all()
            if marks:
                return f"{sum(float(mark.score) for mark in marks):.2f}"
            return "0.00"

    def get_highestScore(self, obj):
        """Get highest score."""
        marks = obj.marks.all()
        if marks:
            return f"{max(float(mark.score) for mark in marks):.2f}"
        return "0.00"

    def get_lowestScore(self, obj):
        """Get lowest score."""
        marks = obj.marks.all()
        if marks:
            return f"{min(float(mark.score) for mark in marks):.2f}"
        return "0.00"


class ReportCardSummarySerializer(ReadBaseSerializer):
    """Lightweight serializer for report card lists without marks."""

    studentReferenceId = serializers.CharField(source="student.id", read_only=True)
    studentName = serializers.CharField(source="student.name", read_only=True)
    term = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True)
    totalSubjects = serializers.IntegerField(read_only=True, source="total_subjects")
    averageScore = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, source="average_score"
    )
    totalScore = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True, source="total_score"
    )
    grade = serializers.CharField(read_only=True)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    calculationStatus = serializers.CharField(source="calculation_status", read_only=True)
    isActive = serializers.BooleanField(source="is_active", read_only=True)


class StudentYearPerformanceSerializer(serializers.Serializer):
    """Serializer for student's yearly performance summary."""

    studentReferenceId = serializers.CharField(
        read_only=True, source="studentreferenceId"
    )
    year = serializers.IntegerField(read_only=True)
    subjectAverages = serializers.SerializerMethodField()
    overallAverage = serializers.CharField(read_only=True, source="overall_average")

    def get_subjectAverages(self, obj):
        """Convert subject averages to camelCase."""
        subject_averages = obj.get("subject_averages", [])
        return [
            {
                "subjectCode": item.get("subject__code"),
                "subjectName": item.get("subject__name"),
                "averageScore": float(item.get("average_score", 0)),
                "termCount": item.get("term_count", 0),
            }
            for item in subject_averages
        ]


class SubjectPerformanceSerializer(serializers.Serializer):
    """Serializer for subject performance statistics."""

    subject_id = serializers.IntegerField(read_only=True)
    year = serializers.IntegerField(read_only=True, required=False)
    average_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    highest_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    lowest_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    total_students = serializers.IntegerField(read_only=True)
    total_marks = serializers.IntegerField(read_only=True)
