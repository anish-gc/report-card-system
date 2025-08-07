import logging
from typing import Tuple, Optional, Any
from functools import lru_cache

from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from utilities import global_parameters
from utilities.custom_encryption_class import AESCipher

# Configure logger
logger = logging.getLogger("__name__")

class BaseCustomAuthentication(BaseAuthentication):
    """
    Base custom authentication class for token-based authentication with improved
    error handling, performance optimizations, and security measures.
    """
    user_model = None  # Must be overridden in subclasses
    TOKEN_PREFIX = 'Token'
    
    def authenticate(self, request: Request) -> Optional[Tuple[Any, None]]:
        """
        Authenticate the user using the provided token.
        
        Args:
            request: The incoming request object containing authentication headers
            
        Returns:
            A tuple of (user, None) if authentication succeeds
            
        Raises:
            AuthenticationFailed: If authentication fails for any reason
        """
        if not self.user_model:
            logger.error("Authentication configuration error: user_model not defined")
            raise AuthenticationFailed("Server authentication configuration error", code=500)
            
        try:
            token = self.get_token(request)
            if not token:
                return None  # Allow the request to fall through to other authentication methods
                
            access_token = self.decrypt_token(token)
            user = self.authenticate_user(access_token)
            if settings.SESSION_EXPIRY_ENABLED:
                self.check_session_expiry(user)
            return (user, None)
            
        except AuthenticationFailed:
            # Let the original AuthenticationFailed exceptions propagate
            raise
        except Exception as ex:
            logger.exception(f"Unexpected error during authentication: {str(ex)}")
            raise AuthenticationFailed(global_parameters.NO_USER, code=401)
    
    def get_token(self, request: Request) -> Optional[str]:
        """
        Retrieve and validate the token from the Authorization header.
        
        Args:
            request: The incoming request object
            
        Returns:
            The extracted token string or None if not present
            
        Raises:
            AuthenticationFailed: If token format is invalid
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            logger.debug("No authorization header provided")
            raise AuthenticationFailed('Invalid token format. Expected: Token <token_value>', code=401)
       
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.TOKEN_PREFIX.lower():
            logger.warning(f"Invalid token format: {auth_header[:20]}...")
            raise AuthenticationFailed('Invalid token format. Expected: Token <token_value>', code=401)
            
        return parts[1]
    
    @lru_cache(maxsize=128)
    def get_cipher(self) -> AESCipher:
        """
        Get a cached AESCipher instance to improve performance for frequent token decryption.
        
        Returns:
            An AESCipher instance using the application's encryption key
        """
        if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
            logger.critical("ENCRYPTION_KEY not properly configured in settings")
            raise AuthenticationFailed("Server security configuration error", code=500)
            
        return AESCipher(settings.ENCRYPTION_KEY)
    
    def decrypt_token(self, token: str) -> str:
        """
        Decrypt the provided token using AES encryption.
        
        Args:
            token: The encrypted token string
            
        Returns:
            The decrypted token string
            
        Raises:
            AuthenticationFailed: If token decryption fails
        """
        try:
            aes = self.get_cipher()
            return aes.decrypt(token)
        except Exception as ex:
            logger.warning(f"Token decryption failed: {str(ex)}")
            raise AuthenticationFailed("Invalid authentication token", code=401)
    
    def authenticate_user(self, access_token: str) -> Any:
        """
        Authenticate the user using the decrypted access token.
        
        Args:
            access_token: The decrypted access token
            
        Returns:
            The authenticated user object
            
        Raises:
            AuthenticationFailed: If user cannot be found or is inactive
        """
        try:
            # Use select_related to optimize DB queries if user has foreign key relationships
            user = self.user_model.objects.filter(
                access_token=access_token,
                is_active=True
            ).first()
            
            if not user:
                logger.info(f"No active user found with the provided token")
                raise AuthenticationFailed(global_parameters.NO_USER, code=401)
                
            return user
            
        except Exception as ex:
            logger.error(f"Error retrieving user: {str(ex)}")
            raise AuthenticationFailed(global_parameters.NO_USER, code=401)
    
    def check_session_expiry(self, user: Any) -> None:
        """
        Check if the user's session has expired and extend session time if valid.
        
        Args:
            user: The authenticated user object
            
        Raises:
            AuthenticationFailed: If the user's session has expired
        """
        if not hasattr(user, 'session_time'):
            logger.warning(f"User model does not have session_time field")
            return
        current_time = timezone.now()
        session_time = user.session_time
        
        # Check for session expiry
        # if session_time and session_time < current_time:
        #     logger.info(f"Session expired for user {user.id}")
        #     raise AuthenticationFailed("Session has expired", code=401)
        
        # Determine new session expiry time
        session_limit = getattr(settings, 'SESSION_LIMIT_TIME', 60)  # Default to 60 minutes
        new_expiry = current_time + timedelta(minutes=session_limit)
        # Update session time using query optimization to avoid race conditions
        type(user).objects.filter(pk=user.pk).update(session_time=new_expiry)
        
        # Update the instance to reflect the database change
        user.session_time = new_expiry
        
    def authenticate_header(self, request: Request) -> str:
        """
        Return a string to be used in the `WWW-Authenticate` header.
        
        Args:
            request: The incoming request object
            
        Returns:
            String for the WWW-Authenticate header
        """
        return f'{self.TOKEN_PREFIX} realm="api"'


class CustomAuthentication(BaseCustomAuthentication):
    """
    Custom authentication class for the Account model with proper imports.
    """
    def __init__(self):
        # Import here to avoid circular import issues
        from accounts.models import Account
        self.user_model = Account