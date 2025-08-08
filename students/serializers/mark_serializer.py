




from utilities.base_serializer import WriteBaseSerializer

from rest_framework import serializers
from students.models import  Mark
from students.models.subject_model import Subject
from students.serializers.subject_serializer import SubjectReadSerializer
from utilities import global_parameters
from utilities.base_serializer import ReadBaseSerializer, WriteBaseSerializer
from utilities.custom_exception_class import CustomAPIException
from decimal import Decimal
import logging

from utilities.global_functions import model_validation

logger = logging.getLogger("django")

class MarkWriteSerializer(WriteBaseSerializer):
    """Optimized serializer for creating/updating marks."""
    
    subject = serializers.UUIDField(
        error_messages={
            "required": "Subject is required.",
            "does_not_exist": "Subject does not exist or is inactive.",
        },
    )
    
    score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=Decimal("100.00"),
        error_messages={
            "required": "Score is required.",
            "invalid": "Score must be a valid decimal number.",
            "min_value": "Score cannot be less than 0.",
            "max_value": "Score cannot be greater than 100.",
        },
    )
    
    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        error_messages={
            "max_length": "Remarks cannot exceed 500 characters.",
        },
    )

    def validate(self, data):
        subject_id = data.get('subject')
        subject_instance = model_validation(Subject, 'Please choose the correct subject', {'id':subject_id})
        return data | {"subject":subject_instance}


    def create(self, validated_data):
        return Mark.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class MarkReadSerializer(ReadBaseSerializer):
    """Optimized read serializer for marks with minimal queries."""
    
    subject = SubjectReadSerializer(read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    remarks = serializers.CharField(read_only=True)


class MarkSummarySerializer(serializers.Serializer):
    """Lightweight serializer for mark summaries without subject details."""
    
    referenceId = serializers.CharField(read_only=True,source='id')
    subjectreferenceId = serializers.CharField(read_only=True,source="subject.id")
    subjectName = serializers.CharField(source="subject.name", read_only=True)
    subjectCode = serializers.CharField(source="subject.code", read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    remarks = serializers.CharField(read_only=True)
