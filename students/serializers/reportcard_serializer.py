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
from utilities.global_functions import validate_unique_fields


class ReportCardWriteSerializer(WriteBaseSerializer):
    """Optimized serializer for creating/updating report cards."""

    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.filter(is_active=True),
        error_messages={
            "required": "Student is required to create reportcard.",
            "does_not_exist": "Student does not exist or is inactive.",
        },
    )

    term = serializers.ChoiceField(
        choices=ReportCard.TERM_CHOICES,
        error_messages={
            "required": "Term is required.",
            "invalid_choice": "Invalid term choice.Please choose Term1, Term2, Term3 or Final",
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
        try:
            student = data.get("student")
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
                    f"Report card for student {student}, term {term}, and year {year} already exists."
                )
            return data
        except CustomAPIException as exe:
            raise serializers.ValidationError(
                {global_parameters.ERROR_DETAILS: [exe.detail]}
            )

        except Exception as exe:
            raise Exception(exe)

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


class ReportCardReadSerializer(ReadBaseSerializer):
    """Optimized read serializer for report cards with all details."""

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
    marks = MarkSummarySerializer(many=True, read_only=True)

    # Calculated fields from annotations (if available)
    calculated_average = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, required=False
    )
    calculated_total = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True, required=False
    )
    subject_count = serializers.IntegerField(read_only=True, required=False)
    highest_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, required=False
    )
    lowest_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, required=False
    )


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
    isActive = serializers.BooleanField(source="is_active", read_only=True)


class StudentYearPerformanceSerializer(serializers.Serializer):
    """Serializer for student's yearly performance summary."""

    student_id = serializers.IntegerField(read_only=True)
    year = serializers.IntegerField(read_only=True)
    subject_averages = serializers.ListField(read_only=True)
    overall_average = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )


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
