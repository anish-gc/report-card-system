from rest_framework.exceptions import APIException, AuthenticationFailed, MethodNotAllowed, PermissionDenied
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from typing import Optional, Dict, Any, Union, TypeVar

from utilities import global_parameters

# Type variable for response data
ResponseData = TypeVar('ResponseData', bound=Dict[str, Any])


class CustomAPIException(APIException):
    """
    Enhanced API exception class with flexible status code support.
    
    This class provides a standardized way to raise API exceptions with
    customizable status codes and detailed error messages.
    
    Attributes:
        detail: The error detail message or structure
        status_code: HTTP status code for the error
    """
    
    def __init__(self, detail: Union[str, Dict[str, Any]], status_code: int = status.HTTP_400_BAD_REQUEST):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AuthenticationFailedError(CustomAPIException):
    """
    Specialized exception for authentication failures.
    
    Provides a consistent way to handle authentication errors with appropriate
    status codes and messages.
    """
    
    def __init__(self, detail: Union[str, Dict[str, Any]] = "Authentication failed", 
                 status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(detail, status_code)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """
    Advanced exception handler for consistent API error responses.
    
    This handler provides standardized error responses for common exception types,
    with appropriate status codes and messages. It falls back to DRF's default
    handler for unhandled exception types.
    
    Args:
        exc: The exception that was raised
        context: The exception context
        
    Returns:
        Response object with standardized error format or None if unhandled
    """
    # Map exception types to handler functions for cleaner code
    exception_handlers = {
        AuthenticationFailed: _handle_authentication_failed,
        MethodNotAllowed: _handle_method_not_allowed,
        PermissionDenied: _handle_permission_denied,
        CustomAPIException: _handle_custom_api_exception,
    }
    # Check for exact type matches first
    handler = exception_handlers.get(type(exc))
    if handler:
        return handler(exc)
    
    # If no exact match, check for instance matches
    for exc_type, handler in exception_handlers.items():
        if isinstance(exc, exc_type):
            return handler(exc)
    
    # Fall back to DRF's exception handler for unhandled exceptions
    response = exception_handler(exc, context)

    # If DRF doesn't handle it, standardize the response ourselves
    if response is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return Response(
            {
                global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
                global_parameters.RESPONSE_MESSAGE: "An unexpected error occurred.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return response


# Specialized exception handlers for cleaner main handler

def _handle_authentication_failed(exc: AuthenticationFailed) -> Response:
    """Handle authentication failed exceptions"""
    return Response(
        {
            global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE_TYPE: global_parameters.RESPONSE_CUSTOM_UNSUCCESS_MESSAGE,
            global_parameters.RESPONSE_MESSAGE: "Authentication credentials were not provided or are invalid.",
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


def _handle_method_not_allowed(exc: MethodNotAllowed) -> Response:
    """Handle method not allowed exceptions"""
    return Response(
        {
            global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE: f"Method not allowed. Please use an appropriate HTTP method. Available methods: {', '.join(exc.available_methods) if hasattr(exc, 'available_methods') and exc.available_methods else 'unknown'}",
        },
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )


def _handle_permission_denied(exc: PermissionDenied) -> Response:
    """Handle permission denied exceptions"""
    return Response(
        {
            global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE: "You do not have the required permission to access this resource.",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _handle_custom_api_exception(exc: CustomAPIException) -> Response:
    """Handle custom API exceptions"""
    return Response(
        {
            global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE: exc.detail,
        },
        status=exc.status_code,
    )