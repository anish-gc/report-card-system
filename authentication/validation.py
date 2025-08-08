import base64
import logging
from functools import lru_cache
from typing import Dict, Tuple,  Any

from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.core.cache import cache
from datetime import timedelta


import uuid

from accounts.models import Account
from utilities.custom_encryption_class import AESCipher
from utilities.custom_exception_class import AuthenticationFailedError, CustomAPIException

def generate_uuid():
    """Generate a unique UUID for reference_id field."""
    return uuid.uuid4().hex

logger = logging.getLogger('django')

# Constants for improved readability and maintainability
SESSION_CACHE_KEY_PREFIX = 'user_session_'
SESSION_CACHE_TIMEOUT = getattr(settings, 'SESSION_CACHE_TIMEOUT', 300)  # 5 minutes default





def login_validation(request: HttpRequest) -> Tuple[str, str]:
    """
    Extract and validate basic authentication credentials from request.
    
    Args:
        request: The HTTP request containing authorization header
        
    Returns:
        Tuple of (username, password)
        
    Raises:
        AuthenticationFailedError: If credentials are invalid or missing
    """
    try:
        # Check if Authorization header exists
        
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            raise AuthenticationFailedError("Authorization header missing")
        
        # Split and validate auth type
        parts = auth_header.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'basic':
            raise AuthenticationFailedError("Invalid authentication type")
        
        # Decode credentials
        try:
            decoded = base64.b64decode(parts[1]).decode('utf-8')
        except Exception:
            raise AuthenticationFailedError(    "Invalid authorization encoding")
        
        # Split username and password
        if ':' not in decoded:
            raise AuthenticationFailedError("Invalid credentials format")
            
        username, password = decoded.split(':', 1)
        
        # Validate minimum requirements
        if not username or not password:
            raise AuthenticationFailedError("Username and password cannot be empty")
            
        return username, password
        
    except AuthenticationFailedError as exc:
        # Re-raise specific authentication errors
        raise CustomAPIException(exc)
    except Exception as e:
        # Log unexpected errors and convert to authentication error
        logger.error(f"Login validation error: {str(e)}", exc_info=True)
        raise AuthenticationFailedError("Invalid credentials")




@lru_cache(maxsize=1)
def get_cipher() -> AESCipher:
    """
    Get cached AESCipher instance to improve performance.
    
    Returns:
        AESCipher instance using the application's encryption key
    """
    return AESCipher(settings.ENCRYPTION_KEY)


def confirm_login_details(request: HttpRequest, user: Account) -> Dict[str, Any]:
    """
    Confirm login details and generate access token with session management.
    
    Args:
        request: The HTTP request
        user: The authenticated user
        
    Returns:
        Dictionary with token and user information
        
    Raises:
        AuthenticationFailedError: If login confirmation fails
    """
    try:
        with transaction.atomic():
            # Handle user session (this may raise exceptions for concurrent logins)
            session_updated = handle_user_session(user, request)
            
            # Get cipher instance from cache
            aes = get_cipher()
            
          
            # Return authentication data
            auth_data = {
                "token": aes.encrypt(user.access_token).decode('utf-8'),
                "designation": 'superadmin',
                "username": user.username,
                "sessionTime": settings.SESSION_LIMIT_TIME,
                "sessionRenewed": session_updated,
            }    

            return auth_data
            
    except AuthenticationFailedError:
        # Re-raise specific authentication errors
        raise
    except Exception as e:
        # Log unexpected errors and convert to authentication error
        logger.error(f"Login confirmation failed: {str(e)}", exc_info=True)
        raise AuthenticationFailedError("Login processing failed")


def handle_user_session(user: Account, request: HttpRequest) -> bool:
    """
    Manage user session with security checks for concurrent logins.
    
    Args:
        user: The authenticated user
        request: The HTTP request
        
    Returns:
        True if session was renewed, False if existing session was valid
        
    Raises:
        AuthenticationFailedError: If session conflicts are detected
    """
    current_time = timezone.now()
    
    # Check for existing valid session
    if user.access_token and user.session_time and current_time < user.session_time:
        # Uncomment to enable concurrent login detection
        # handle_concurrent_login(user, request)
        # For now, we'll just return without updating session
        return False
            
    # Update session with new token and time
    update_session(user, current_time)
    
    # Check for other active sessions with this account
    check_existing_sessions(user)
    
    return True


def update_session(user: Account, current_time: timezone.datetime) -> None:
    """
    Update user session with new token and expiration time.
    
    Args:
        user: The user account to update
        current_time: The current timestamp
    """
    # Generate a secure token
    new_token = generate_uuid()
    new_session_time = current_time + timedelta(minutes=settings.SESSION_LIMIT_TIME)
    
    # Update user with new session data
    user.access_token = new_token
    user.session_time = new_session_time
    
    # Only update necessary fields for performance
    user.save(update_fields=['access_token', 'session_time'])
    
    # Cache the session for faster lookups
    cache_key = f"{SESSION_CACHE_KEY_PREFIX}{user.id}"
    cache.set(cache_key, {
        'token': new_token,
        'expires': new_session_time
    }, timeout=settings.SESSION_LIMIT_TIME * 60)


def handle_concurrent_login(user: Account, request: HttpRequest) -> None:
    """
    Handle concurrent login attempts with security notifications.
    
    Args:
        user: The user account
        request: The HTTP request
        
    Raises:
        AuthenticationFailedError: Always raises to prevent concurrent login
    """
    
    # Prepare device details for email notification
  
    # Log security incident
    logger.warning(f"Concurrent login attempt for user {user.id}")
    
    # Prevent concurrent login
    raise AuthenticationFailedError("Session already active. Please logout from other devices first.")


def check_existing_sessions(user: Account) -> None:
    """
    Check for existing valid sessions with the same account.
    
    Args:
        user: The authenticated user
        
    Raises:
        AuthenticationFailedError: If other active sessions are found
    """
    # Optimize query to only check necessary fields
    concurrent_sessions = Account.objects.filter(
        username=user.username, 
        is_active=True,
        session_time__gt=timezone.now(),
        access_token__isnull=False
    ).exclude(pk=user.pk).exists()
    if concurrent_sessions:
        logger.warning(f"Multiple active sessions detected for account {user.email}")
        raise AuthenticationFailedError("Account already in use elsewhere. Please log out from other devices first.")


def invalidate_user_session(user_id: str) -> None:
    """
    Invalidate a user's session both in database and cache.
    
    Args:
        user_id: The user's reference ID
    """
    try:
        # Clear cache first
        cache_key = f"{SESSION_CACHE_KEY_PREFIX}{user_id}"
        cache.delete(cache_key)
        
        # Then update database
        Account.objects.filter(id=user_id).update(
            access_token=None,
            session_time=None
        )
        
        logger.info(f"Session invalidated for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate session for user {user_id}: {str(e)}")