from rest_framework import serializers
from students.models.subject_model import Subject
from utilities import global_parameters
from utilities.base_serializer import ReadBaseSerializer, WriteBaseSerializer
from utilities.custom_exception_class import CustomAPIException
from utilities.global_functions import validate_unique_fields
import re


class SubjectSerializer(WriteBaseSerializer):
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "required": "Subject name is required.",
            "blank": "Subject name cannot be blank.",
            "max_length": "Subject name cannot exceed 100 characters.",
        },
    )

    code = serializers.CharField(
        max_length=10,
        error_messages={
            "required": "Subject code is required.",
            "blank": "Subject code cannot be blank.",
            "max_length": "Subject code cannot exceed 10 characters.",
        },
    )

    def validate(self, data):

        code = data.get("code", "")
        if not re.match(r"^[A-Z]{2,4}[0-9]{2,4}$", code):
            raise CustomAPIException(
                "Subject code must be 2-4 uppercase letters followed by 2-4 numbers (e.g., MATH101)."
            )

        validate_unique_fields(Subject, data, ["code"], self.instance, "Subject")
        return data

    def create(self, validated_data):
        return Subject.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SubjectReadSerializer(ReadBaseSerializer):
    name = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    isActive = serializers.BooleanField(source="is_active", read_only=True)
