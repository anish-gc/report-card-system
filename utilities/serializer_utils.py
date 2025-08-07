"""
Validation Utilities Module

This module provides standardized validation functions for common data types
and business rules across the application. Each validator follows consistent
patterns for error handling and return values.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union, TypeVar, cast, Set

from django.db.models import Model, QuerySet

from utilities.custom_exception_class import CustomAPIException



# Type definitions
ModelType = TypeVar('ModelType', bound=Model)


def is_numeric_present(value: str) -> bool:
    """
    Check if a string contains at least one numeric digit.
    
    Args:
        value: String to check for numeric digits
        
    Returns:
        True if string contains at least one digit, False otherwise
    """
    return any(char.isdigit() for char in value)


def validate_string_with_dot(input_str: str) -> bool:
    """
    Validate that a string represents a decimal number.
    
    Args:
        input_str: String to validate
        
    Returns:
        True if string matches decimal pattern, False otherwise
    """
    pattern = r'^\d*\.?\d*$'
    return bool(re.match(pattern, input_str))


def is_integer(
    value: str, 
    error_message: str, 
    is_null: bool = False, 
    is_null_msg: Optional[str] = None
) -> bool:
    """
    Validate that a value is an integer string.
    
    Args:
        value: Value to validate
        error_message: Error message to raise if validation fails
        is_null: If True, empty values are considered valid
        is_null_msg: Custom error message for null value validation
        
    Returns:
        True if validation passes
        
    Raises:
        CustomAPIException: If validation fails
    """
    # Handle null case
    if not value:
        if is_null:
            return True
        raise CustomAPIException(is_null_msg or "Value cannot be blank.")
    
    # Validate integer pattern
    if not re.match(r"^[0-9]+$", str(value)):
        raise CustomAPIException(error_message)
    
    return True


def validate_numeric_value(
    value: str, 
    max_digits: int, 
    decimal_places: int, 
    error_message: str, 
    allow_null: bool = False, 
    is_null_msg: Optional[str] = None
) -> bool:
    """
    Validate that a value is a numeric string with specified constraints.
    
    Args:
        value: Value to validate
        max_digits: Maximum total digits allowed
        decimal_places: Maximum decimal places allowed
        error_message: Error message to raise if validation fails
        allow_null: If True, empty values are considered valid
        is_null_msg: Custom error message for null value validation
        
    Returns:
        True if validation passes
        
    Raises:
        CustomAPIException: If validation fails
    """
    # Handle null case
    if not value:
        if allow_null:
            return True
        raise CustomAPIException(is_null_msg or "Value cannot be blank.")
    
    # Construct pattern to match valid numeric strings
    pattern = r'^\d{1,%d}(?:\.\d{1,%d})?$' % (max_digits, decimal_places)
    
    if not re.match(pattern, str(value)):
        raise CustomAPIException(error_message)
    
    return True


def validate_percentage(
    percent_value: str,
    error_message: str,
    invalid_pattern_msg: str
) -> bool:
    """
    Validate that a string represents a valid percentage value.
    
    Args:
        percent_value: Value to validate
        error_message: Error message for invalid decimal format
        invalid_pattern_msg: Error message for invalid percentage pattern
        
    Returns:
        True if validation passes
        
    Raises:
        CustomAPIException: If validation fails
    """
    # First validate it's a decimal number
    if not validate_string_with_dot(percent_value):
        raise CustomAPIException(error_message)
    
    # Then validate specific percentage pattern (up to 3 decimal places)
    pattern = r'^\d+(\.\d{1,3})?$'
    if not re.match(pattern, percent_value):
        raise CustomAPIException(invalid_pattern_msg)
    
    return True


def validate_unique_fields(
    model: Type[ModelType],
    data: Dict[str, Any],
    unique_fields: List[str],
    instance: Optional[ModelType] = None,
    model_name: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
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







def validate_date_range(
    start_date: str, 
    end_date: str, 
    date_format: str = '%Y-%m-%d'
) -> tuple[datetime, datetime]:
    """
    Validate a date range and convert string dates to datetime objects.
    
    Args:
        start_date: Start date in string format
        end_date: End date in string format
        date_format: Format string for datetime parsing (default: YYYY-MM-DD)
        
    Returns:
        Tuple of (start_date, end_date) as datetime objects
        
    Raises:
        CustomAPIException: If dates are invalid or end_date precedes start_date
    """
    try:
        # Parse start date
        try:
            start_date_obj = datetime.strptime(start_date, date_format)
        except ValueError:
            raise CustomAPIException("Invalid start date format. Expected YYYY-MM-DD.")
        
        # Parse end date
        try:
            end_date_obj = datetime.strptime(end_date, date_format)
        except ValueError:
            raise CustomAPIException("Invalid end date format. Expected YYYY-MM-DD.")
        
        # Validate date order
        if end_date_obj < start_date_obj:
            raise CustomAPIException("End date must be on or after start date.")
        
        return start_date_obj, end_date_obj
        
    except CustomAPIException:
        # Re-raise custom exceptions as-is
        raise
    except Exception as exc:
        # Catch and convert any other exceptions
        raise CustomAPIException(f"Date validation error: {str(exc)}")