
from rest_framework import serializers
from datetime import datetime

from utilities.custom_exception_class import CustomAPIException

class ReadBaseSerializer(serializers.Serializer):
    referenceId = serializers.CharField(source="id", read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

class WriteBaseSerializer(serializers.Serializer):
    def save(self, **kwargs):
        request = self.context.get('request')
        validated_data = self.validated_data.copy()

        if not request or not request.user:
            raise CustomAPIException("User must be provided.")

        if request and request.user:
            if self.instance is None:  # New instance
                validated_data['created_by'] = request.user
                validated_data['created_at'] = datetime.now()
            else:
                validated_data['updated_by'] = request.user
                validated_data['updated_at'] = datetime.now()

        return super().save(**validated_data, **kwargs)