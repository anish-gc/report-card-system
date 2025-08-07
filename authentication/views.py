import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from typing import Dict, Any

from accounts.models import Account
from authentication.validation import (
    confirm_login_details,
    login_validation,
)
from utilities import global_parameters
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView


logger = logging.getLogger(__name__)


class LoginApiView(APIView):
    """
    Handles user login and authentication with comprehensive security measures.

    This view authenticates users based on provided credentials and manages
    session generation with proper security controls.
    """

    authentication_classes = []  # No authentication needed for login
    permission_classes = []  # No permissions needed for login
    throttle_scope = "login"  # Apply rate limiting for security

    @method_decorator(never_cache)
    def post(self, request) -> Response:
        """
        Authenticate user and return login response with proper token and session info.

        Args:
            request: HTTP request containing authentication credentials

        Returns:
            Response with authentication token and user details on success,
            or error details on failure
        """
        try:
            # Extract and validate credentials
            username, password = login_validation(request)

            # Authenticate user against Django's authentication system
            user = authenticate(request, username=username, password=password)
            if not user:
                logger.warning(f"Login failed for username: {username}")
                return self._create_error_response(
                    global_parameters.NO_USER, status_code=status.HTTP_401_UNAUTHORIZED
                )


            # Process login and generate session data
            login_data = confirm_login_details(request, user)

            return self._create_success_response(
                login_data, global_parameters.LOGIN_RESPONSE_SUCCESS_MESSAGE
            )

        except CustomAPIException as exc:
            logger.error(f"Authentication error: {str(exc)}", exc_info=True)
            status_code = getattr(exc, "status_code", status.HTTP_401_UNAUTHORIZED)
            return self._create_error_response(str(exc), status_code)

        except Exception as exc:
            logger.error(f"Unexpected login error: {str(exc)}", exc_info=True)
            return self._create_error_response(
                global_parameters.NO_USER,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _create_success_response(self, data: Dict[str, Any], message: str) -> Response:
        """
        Create a standardized success response with consistent structure.

        Args:
            data: The data payload to return to the client
            message: Success message for the response

        Returns:
            Formatted HTTP response
        """
        response_data = {
            global_parameters.RESPONSE_CODE: global_parameters.SUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE: message,
            global_parameters.DATA: data,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def _create_error_response(
        self, error_message: str, status_code: int = status.HTTP_401_UNAUTHORIZED
    ) -> Response:
        """
        Create a standardized error response with appropriate status code.

        Args:
            error_message: The error message to display
            status_code: HTTP status code to return (default 401)

        Returns:
            Formatted HTTP error response
        """
        response_data = {
            global_parameters.RESPONSE_CODE: global_parameters.UNSUCCESS_CODE,
            global_parameters.RESPONSE_MESSAGE_TYPE: global_parameters.RESPONSE_CUSTOM_UNSUCCESS_MESSAGE,
            global_parameters.RESPONSE_MESSAGE: error_message,
        }
        return Response(response_data, status=status_code)


class LogoutApiView(BaseApiView):
    """
    Handles user logout by invalidating the access token and terminating the session.

    This view ensures secure logout with proper token invalidation and
    session cleanup to prevent session fixation attacks.
    """

    required_permissions = []  # No specific permissions needed for logout

    @transaction.atomic
    @method_decorator(never_cache)
    def delete(self, request) -> Response:
        """
        Log out the user by clearing their access token and session data.

        Args:
            request: HTTP request from the authenticated user

        Returns:
            Response indicating logout success or failure
        """
        try:
            # Fetch user with exclusive lock to prevent race conditions
            user = Account.objects.select_for_update().get(
                id=request.user.id, is_active=True
            )

            # Log the logout action before token removal

            # Clear authentication data
            user.access_token = None
            user.session_time = None  # Also clear session time for complete logout
            user.save(update_fields=["access_token", "session_time"])

            # Return success response
            return self.handle_success(
                "You have been successfully logged out from this system."
            )

        except Account.DoesNotExist:
            logger.error(
                f"Logout failed: User {getattr(request.user, 'id', 'unknown')} not found"
            )
            return self.handle_does_not_exist("User not found or already logged out.")

        except Exception as exc:
            logger.error(f"Unexpected error during logout: {str(exc)}", exc_info=True)
            return self.handle_view_exception(exc)
