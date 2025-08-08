"""
Global API response parameters and standardized response objects.

This module defines constants and standard response templates used across
the API to ensure consistent response formats and error handling.
"""

import logging
from typing import Dict, Any, Final

# Configure logger
logger = logging.getLogger("django")

# =============================================================================
# Response Field Names
# =============================================================================

#: Field name for the numeric response code in API responses
RESPONSE_CODE: Final[str] = "responseCode"

#: Field name for the human-readable response message
RESPONSE_MESSAGE: Final[str] = "message"
RESPONSE_MESSAGE_TYPE: Final[str] = "response"
#: Field name for detailed error information in error responses
ERROR_DETAILS: Final[str] = "error"

#: Field name for the main data payload in successful responses
DATA: Final[str] = "data"

#: Field name for paginated data collections (deprecated - now using root level pagination)
PAGINATED_DATA: Final[str] = "paginatedData"

# =============================================================================
# Response Code Values
# =============================================================================

#: Response code indicating success (string '0' for legacy compatibility)
SUCCESS_CODE: Final[str] = '0'

#: Response code indicating failure (string '1' for legacy compatibility)
UNSUCCESS_CODE: Final[str] = '1'

# =============================================================================
# Standard Response Messages
# =============================================================================

#: Standard success message
RESPONSE_SUCCESS_MESSAGE: Final[str] = "ok"

#: Standard failure message
RESPONSE_UNSUCCESS_MESSAGE: Final[str] = "failed"

#: Message for custom error responses
RESPONSE_CUSTOM_UNSUCCESS_MESSAGE: Final[str] = "customResponse"
# RESPONSE_CUSTOM_SERIALIZER_UNSUCCESS_MESSAGE: Final[str] = "customFieldResponse"

#: Message for successful login
LOGIN_RESPONSE_SUCCESS_MESSAGE: Final[str] = "You are logged in successfully"

#: Message for user not found
NO_USER: Final[str] = "We couldnot find the account with given username"

#: Message for attempted deletion of predefined groups
PRE_DEFINED_DELETE_MSG: Final[str] = "Predefined groups cannot be deleted"

# =============================================================================
# Standard Response Templates
# =============================================================================

#: Standard error response template
UNSUCCESS_JSON: Final[Dict[str, str]] = {
    RESPONSE_CODE: UNSUCCESS_CODE,
    RESPONSE_MESSAGE_TYPE: RESPONSE_UNSUCCESS_MESSAGE
}

# 
# UNSUCCESS_SERIALIZER_JSON: Final[Dict[str, str]] = {
#     RESPONSE_CODE: UNSUCCESS_CODE,
#     RESPONSE_MESSAGE_TYPE: RESPONSE_CUSTOM_SERIALIZER_UNSUCCESS_MESSAGE
# }
#: Template for custom error responses
UNSUCCESS_CUSTOM_JSON: Final[Dict[str, str]] = {
    RESPONSE_CODE: UNSUCCESS_CODE,
    RESPONSE_MESSAGE_TYPE: RESPONSE_CUSTOM_UNSUCCESS_MESSAGE  # Fixed typo in original
}

#: Template for internal server errors
INTERNAL_SERVER_ERROR_JSON: Final[Dict[str, str]] = {
    RESPONSE_CODE: UNSUCCESS_CODE,
    RESPONSE_MESSAGE: "Oops! Something went wrong."
}

#: Standard success response template
SUCCESS_JSON: Final[Dict[str, str]] = {
    RESPONSE_CODE: SUCCESS_CODE,
    RESPONSE_MESSAGE: RESPONSE_SUCCESS_MESSAGE
}

#: Response for empty request body
BODY_NOT_BLANK_JSON: Final[Dict[str, str]] = {
    RESPONSE_CODE: UNSUCCESS_CODE,
    RESPONSE_MESSAGE_TYPE: RESPONSE_CUSTOM_UNSUCCESS_MESSAGE,
    RESPONSE_MESSAGE: "Please fill the form to continue."  # Fixed grammar
}