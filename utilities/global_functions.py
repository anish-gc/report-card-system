from utilities.custom_exception_class import CustomAPIException
from typing import Any, Dict, List, Optional, Type, TypeVar
from django.db.models import Model


ModelType = TypeVar("ModelType", bound=Model)


def validate_unique_fields(
    model: Type[ModelType],
    data: Dict[str, Any],
    unique_fields: List[str],
    instance: Optional[ModelType] = None,
    model_name: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Ensure specified fields in the data are unique for the model.

    Args:
        model: Django model class to query against
        data: Dictionary containing field values to validate
        unique_fields: List of field names to check for uniqueness
        instance: Optional instance to exclude from uniqueness check (for updates)
        model_name: Human-readable model name for error messages
        filters: Additional filters to apply to uniqueness query

    Returns:
        True if all fields are unique

    Raises:
        CustomAPIException: If any field value violates uniqueness constraint
    """
    filters = filters or {}
    model_name = model_name or "Record"

    for field in unique_fields:
        # Skip fields not present in data
        if field not in data:
            continue

        value = data[field]

        # Skip empty values
        if value is None or value == "":
            continue

        # Build query with active filter and any additional filters
        query = model.objects.filter(**{field: value}, **filters)

        # Exclude current instance from check if provided
        if instance:
            query = query.exclude(id=instance.id)

        # Raise exception if duplicate found
        if query.exists():
            field_label = field.replace("_", " ").title()
            raise CustomAPIException(
                f"{model_name} with {field_label} '{value}' already exists."
            )

    return True
