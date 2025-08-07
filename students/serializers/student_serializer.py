from rest_framework import serializers
from django.utils import timezone
from students.models.student_model import Student
from utilities import global_parameters
from utilities.base_serializer import ReadBaseSerializer, WriteBaseSerializer
from utilities.custom_exception_class import CustomAPIException
from utilities.global_functions import validate_unique_fields


class StudentSerializer(WriteBaseSerializer):
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "required": "Student name is required.",
            "blank": "Student name cannot be blank.",
            "max_length": "Student name cannot exceed 100 characters.",
        },
    )

    email = serializers.EmailField(
        error_messages={
            "required": "Email address is required.",
            "blank": "Email address cannot be blank.",
            "invalid": "Please enter a valid email address.",
        }
    )

    dateOfBirth = serializers.DateField(
        source="date_of_birth",
        error_messages={
            "required": "Date of birth is required.",
            "invalid": "Please enter a valid date in YYYY-MM-DD format.",
        },
    )

    isActive = serializers.BooleanField(
        source="is_active",
        default=True,
        error_messages={
            "invalid": "Please provide a valid boolean value for active status."
        },
    )

    def validate(self, data):

        try:
            date_of_birth = data.get("date_of_birth")
            if date_of_birth and date_of_birth > timezone.now().date():
                raise CustomAPIException("Date of birth cannot be in the future.")
            validate_unique_fields(Student, data, ["email"], self.instance, "Student")

            return data
        except CustomAPIException as exe:
            raise serializers.ValidationError(
                {global_parameters.ERROR_DETAILS: [exe.detail]}
            )

        except Exception as exe:
            raise Exception(exe)

    def create(self, validated_data):
        return Student.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StudentReadSerializer(ReadBaseSerializer):
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    dateOfBirth = serializers.DateField(source="date_of_birth", read_only=True)
