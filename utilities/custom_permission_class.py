from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.utils.text import camel_case_to_spaces
from django.contrib.auth.models import Permission, User
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings

from typing import List, Set, Dict, Any, Optional, Type, ClassVar
import logging

from utilities import global_parameters
from utilities.custom_response_class import HandleResponseMixin

logger = logging.getLogger(__name__)

# Cache timeout for permission sets (5 minutes by default)
PERMISSION_CACHE_TIMEOUT = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 300)


class CustomPermission(BasePermission):
    """
    Enhanced permission system with caching and optimized permission checks.
    
    This class provides efficient permission checking against user permissions,
    with support for:
    - Cached permission lookups
    - Group-based permissions
    - Superuser bypass
    - Optimized database queries
    
    Usage:
        class MyView(APIView):
            permission_classes = [CustomPermission]
            required_permissions = ['view_mymodel', 'change_mymodel']
    """
    
    @staticmethod
    def get_user_permissions(user: User) -> Set[str]:
        """
        Get all permissions for a user with caching.
        
        This method retrieves and caches permission codenames for a user
        to minimize database queries.
        
        Args:
            user: The user to get permissions for
            
        Returns:
            Set of permission codenames for the user
        """
        if not user or not user.is_authenticated:
            return set()
            
        # Use cache to avoid repeated DB queries
        cache_key = f'user_permissions_{user.id}'
        cached_permissions = cache.get(cache_key)
        
        if cached_permissions is not None:
            return cached_permissions
            
        # Get direct user permissions
        user_permissions = set(user.user_permissions.values_list("codename", flat=True))
        
        # Get group permissions
        group_permissions = set(
            Permission.objects.filter(roles__accounts=user).values_list("codename", flat=True)
        )
        
        # Combine both permission sets
        all_permissions = user_permissions | group_permissions
        
        # Cache the result
        cache.set(cache_key, all_permissions, PERMISSION_CACHE_TIMEOUT)
        
        return all_permissions

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user has any of the required permissions.
        
        Args:
            request: The current request
            view: The view being accessed
            
        Returns:
            True if the user has required permissions, False otherwise
        """
        # Get required permissions from view
        required_permissions = getattr(view, "required_permissions", [])
        
        # Skip permission check if no permissions required
        if not required_permissions:
            return True
        
        # Superusers always have all permissions
        if request.user.is_superuser:
            return True
            
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Get all user permissions
        user_permissions = self.get_user_permissions(request.user)
        
        # Check if user has any of the required permissions
        return bool(user_permissions.intersection(required_permissions))


class CustomPermissionMixin:
    """
    Mixin for dynamic permission configuration based on model and HTTP method.
    
    This mixin automatically configures required permissions based on the model
    name and HTTP method, following Django's permission naming convention.
    """
    required_permissions: ClassVar[List[str]] = []

    def get_permissions(self) -> List[BasePermission]:
        """
        Get permission classes with CustomPermission added when needed.
        
        Returns:
            List of permission class instances
        """
        permission_classes = list(getattr(self, 'permission_classes', []))
        
        # Add CustomPermission if required_permissions are specified
        if self.required_permissions:
            if CustomPermission not in permission_classes:
                permission_classes.append(CustomPermission)
                
        return [permission() for permission in permission_classes]


class BaseApiView(CustomPermissionMixin, HandleResponseMixin):
    """
    Base API view with advanced permission handling and response formatting.
    
    This class provides:
    - Dynamic permission configuration
    - Standard authentication
    - Request validation
    - Database table name verification
    
    Subclasses must define:
    - db_table_name: The database table name for permission mapping
    """
    permission_classes: ClassVar[List[Type[BasePermission]]] = []
    
    # Cache for snake_case conversions to improve performance
    _snake_case_cache: Dict[str, str] = {}

    def __init__(self, **kwargs):
        # Import APIView here to avoid circular imports at module level
        from rest_framework.views import APIView
        
        # Dynamically inherit from APIView
        if not any(issubclass(cls, APIView) for cls in self.__class__.__mro__):
            # If APIView is not in the MRO, we need to ensure proper initialization
            # This is a workaround for the circular import issue
            super().__init__(**kwargs)
        else:
            super().__init__(**kwargs)

    def get_permissions(self) -> List[BasePermission]:
        """
        Dynamically set required permissions based on the request method and model name.
        
        Returns:
            List of permission class instances
        """
        if not hasattr(self, 'db_table_name') or not self.db_table_name:
            raise ValueError(
                f"{self.__class__.__name__} must define a db_table_name attribute."
            )
            
        # Get snake_case model name (with caching for performance)
        model_name = self.db_table_name
        if model_name not in self._snake_case_cache:
            snake_case_model_name = camel_case_to_spaces(model_name).replace(' ', '_').lower()
            self._snake_case_cache[model_name] = snake_case_model_name
        else:
            snake_case_model_name = self._snake_case_cache[model_name]

        # Map HTTP methods to permission codenames
        method_permissions_map = {
            "GET": f"view_{snake_case_model_name}",
            "POST": f"add_{snake_case_model_name}",
            "PUT": f"change_{snake_case_model_name}",
            "PATCH": f"change_{snake_case_model_name}",
            "DELETE": f"delete_{snake_case_model_name}",
        }

        # Set required permission based on request method
        permission_codename = method_permissions_map.get(self.request.method)
        if permission_codename:
            self.required_permissions = [permission_codename]
            
        # Get permission classes from parent
        return super().get_permissions()

    def validate_request_body(self, request: Request) -> Optional[Response]:
        """
        Validate that the request body is not empty for methods that require it.
        
        This method ensures PUT, POST, and PATCH requests contain a valid body.
        GET and DELETE requests are allowed to have empty bodies.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            Response object with error details if validation fails, None otherwise
        """
        # Skip validation for methods that don't require a body
        if request.method in ['GET', 'DELETE']:
            return None
            
        # Check if body exists and is not empty
        if not request.body or not request.data:
            return Response(
                global_parameters.BODY_NOT_BLANK_JSON, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return None

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Create a view callable from this class.
        This method dynamically imports APIView to avoid circular imports.
        """
        from rest_framework.views import APIView
        
        # Create a new class that inherits from both APIView and this class
        class_name = f"{cls.__name__}WithAPIView"
        new_class = type(class_name, (APIView, cls), {})
        
        # Use APIView's as_view method
        return new_class.as_view(**initkwargs)