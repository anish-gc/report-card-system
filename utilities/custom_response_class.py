import logging
from typing import Any, Dict, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from utilities import global_parameters
from utilities.custom_pagination_class import CustomPagination
from utilities.global_parameters import (
    DATA,
    ERROR_DETAILS,
    INTERNAL_SERVER_ERROR_JSON,
    RESPONSE_MESSAGE,
    SUCCESS_JSON,
    UNSUCCESS_CUSTOM_JSON,
    UNSUCCESS_JSON,
)

logger = logging.getLogger("django")


class HandleResponseMixin:
    """
    Mixin to standardize API response handling and exception management.
    
    This mixin provides consistent methods for formatting API responses across
    multiple view classes, supporting:
    
    - Success responses with optional data payloads
    - Paginated data responses with metadata
    - Standardized error responses (400, 404, 500)
    - Exception handling with appropriate logging
    - Serializer validation error handling
    
    All methods maintain consistent response structure for the API contract.
    """

    @staticmethod
    def handle_success(
        success_message: str, 
        data: Optional[Any] = None
    ) -> Response:
        """
        Create a standardized success response with an optional data payload.
        
        Args:
            success_message: Human-readable success message for the response
            data: Optional data payload to include in the response
            
        Returns:
            Response object with 200 status code and standardized structure
        """
        response_data = SUCCESS_JSON.copy()
        response_data[RESPONSE_MESSAGE] = success_message
        
        if data is not None:
            response_data[DATA] = data
            
        return Response(response_data, status=status.HTTP_200_OK)


    def handle_serializer_data(self, model, serializer_class, many=True, paginate=True, **query):
        """
        Handle responses with serialized data, optionally with pagination.
        
        Args:
            model (Model): The Django model to query
            serializer_class (Serializer): The serializer class to use
            many (bool): Whether to handle multiple objects (default True)
            paginate (bool): Whether to paginate results (default True)
            **query: Additional query parameters for filtering
            
        Returns:
            Response with serialized data, optionally paginated
        """
        try:
            if many:
                queryset = model.objects.filter(**query)
                
                if paginate:
                    # Initialize paginator
                    paginator = CustomPagination()
                    
                    # Paginate the queryset
                    page = paginator.paginate_queryset(queryset, self.request)
                    
                    if page is not None:
                        # Serialize the page
                        serializer = serializer_class(page, many=True)
                        return paginator.get_paginated_response(serializer.data)
                
                # Fallback for non-paginated responses
                serialized_data = serializer_class(queryset, many=True).data
            else:
                model_instance = model.objects.get(**query)
                serialized_data = serializer_class(model_instance).data
            
            message = global_parameters.SUCCESS_JSON | {global_parameters.DATA: serialized_data}
            return Response(message, status=status.HTTP_200_OK)
        
        except Exception as exe:
            return self.handle_view_exception(exe)
    @staticmethod
    def api_handle_exception() -> Response:
        """
        Create a standardized internal server error response.
        
        Returns:
            Response object with 500 status code and standard error message
        """
        return Response(
            INTERNAL_SERVER_ERROR_JSON, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

    @staticmethod
    def handle_invalid_serializer(serializer: Serializer) -> Response:
        """
        Create a standardized response for serializer validation errors.
        
        This method logs the validation errors for debugging and returns
        a properly formatted 400 response with just the first error message.
        
        Args:
            serializer: The serializer instance containing validation errors
            
        Returns:
            Response object with 400 status code and first validation error
        """
        logger.error(f"Serializer validation failed: {serializer.errors}", exc_info=True)
        
        # Get the first error message from the serializer errors
        first_error = None
        for field_errors in serializer.errors.values():
            if field_errors:
                first_error = str(field_errors[0])  # Convert ErrorDetail to string
                break
        
        response_data = {
            "responseCode": "1",
            "response": "customFieldResponse",
            "error": first_error if first_error else "Validation error occurred"
        }
        
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def handle_custom_api_exception(exc: Exception) -> Response:
        """
        Create a standardized response for custom API exceptions.
        
        Args:
            exc: Exception instance with 'detail' and 'status_code' attributes
            
        Returns:
            Response object with the exception's status code and error details
        """
        logger.error(f"Custom API exception: {str(exc)}", exc_info=True)
        
        response_data = UNSUCCESS_CUSTOM_JSON.copy()
        response_data[ERROR_DETAILS] = getattr(exc, 'detail', str(exc))
        status_code = getattr(exc, 'status_code', status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status_code)

    @staticmethod
    def handle_does_not_exist(message: str) -> Response:
        """
        Create a standardized response for "not found" scenarios.
        
        Args:
            message: Description of the resource that wasn't found
            
        Returns:
            Response object with 404 status code and error details
        """
        response_data = UNSUCCESS_JSON.copy()
        response_data[ERROR_DETAILS] = message
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    
    def handle_view_exception(self, exc: Exception) -> Response:
        """
        Route exceptions to appropriate handlers based on exception type.
        
        This central exception handler delegates to specialized handlers
        based on the exception class, maintaining consistent error responses.
        
        Args:
            exc: The exception that was raised
            
        Returns:
            Response object with appropriate status code and error details
        """
        logger.error(f"View exception: {str(exc)}", exc_info=True)
        
        if isinstance(exc, (ObjectDoesNotExist, Http404)):
            return self.handle_does_not_exist(str(exc))
        # Handle DRF's APIException if needed
        if hasattr(exc, 'detail') and hasattr(exc, 'status_code'):
            return self.handle_custom_api_exception(exc)
            
        # Fall back to general server error
        return self.api_handle_exception()