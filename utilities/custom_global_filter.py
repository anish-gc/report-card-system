from django.db.models import Q, Model, Field, QuerySet
import datetime
from decimal import Decimal
import re
from typing import Dict, Any, List, Set, Union, Optional, Tuple, Type, cast
import functools
import logging

logger = logging.getLogger(__name__)


class GlobalFilter:
    """
    Advanced universal filter system for Django models.
    
    This class provides sophisticated filtering capabilities for Django querysets
    with automatic type conversion, field validation, and query optimization.
    
    Features:
    - Automatic type conversion based on model field types
    - Support for complex lookups (comparison, range, etc.)
    - Case-insensitive field name matching (camelCase to snake_case)
    - Validation of field names and lookup types
    - Performance optimizations for repeated operations
    
    Example usage:
        global_filter = GlobalFilter(
            queryset=User.objects.all(),
            model=User,
            request_params=request.GET
        )
        filtered_queryset = queryset.filter(global_filter.build_filters())
    """
    # Class-level caches for performance optimization
    _field_cache: Dict[Type[Model], Dict[str, Field]] = {}
    
    def __init__(self, queryset: QuerySet, model: Type[Model], request_params: Dict[str, str]):
        """
        Initialize the filter with queryset, model, and request parameters.
        
        Args:
            queryset: Base Django queryset to filter
            model: Django model class
            request_params: Dictionary of filter parameters (usually from request.GET)
        """
        self.queryset = queryset
        self.model = model
        self.request_params = request_params
        
        # Valid lookup types supported by this filter
        self.valid_lookups: Set[str] = {
            'exact', 'iexact', 'contains', 'icontains',
            'gt', 'gte', 'lt', 'lte', 'startswith', 'endswith',
            'istartswith', 'iendswith', 'range', 'isnull', 'in'
        }
        
        # Date formats to try when parsing date strings
        self.date_formats: List[str] = [
            '%Y-%m-%d', 
            '%Y-%m-%dT%H:%M:%S', 
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        # Initialize field cache for performance
        self._init_field_cache()
        
    def _init_field_cache(self) -> None:
        """
        Initialize or retrieve field cache for the model.
        
        This improves performance by caching model field information at the class level.
        """
        if self.model not in self._field_cache:
            # Get all field information for the model
            field_dict = {f.name: f for f in self.model._meta.get_fields()}
            
            # Add snake_case to camelCase mapping for case-insensitive matching
            camel_to_snake = {}
            for field_name in field_dict.keys():
                camel_name = self._to_camel_case(field_name)
                if camel_name != field_name:
                    camel_to_snake[camel_name] = field_name
            
            # Store both direct and transformed mappings
            self._field_cache[self.model] = {**field_dict, **camel_to_snake}
        
        # Set instance field cache from class cache
        self.fields = self._field_cache[self.model]

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _to_snake_case(camel_str: str) -> str:
        """
        Convert camelCase to snake_case with caching for performance.
        
        Args:
            camel_str: String in camelCase format
            
        Returns:
            Equivalent string in snake_case format
        """
        # Insert underscore before each capital letter and convert to lowercase
        snake_str = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
        return snake_str

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def _to_camel_case(snake_str: str) -> str:
        """
        Convert snake_case to camelCase with caching for performance.
        
        Args:
            snake_str: String in snake_case format
            
        Returns:
            Equivalent string in camelCase format
        """
        # Split on underscores, capitalize each component (except first), and join
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def _resolve_field_name(self, field_name: str) -> Optional[str]:
        """
        Resolve a field name to its actual model field name.
        
        This allows case-insensitive field matching and supports both
        camelCase and snake_case naming conventions.
        
        Args:
            field_name: Field name from request parameter
            
        Returns:
            Actual model field name or None if not found
        """
        # Direct match
        if field_name in self.fields:
            return field_name
        
        # Try snake_case conversion
        snake_name = self._to_snake_case(field_name)
        if snake_name in self.fields:
            return snake_name
            
        # Not found
        return None

    def _parse_value(
        self, value: str, field: Field, lookup: str
    ) -> Union[str, int, float, bool, datetime.date, datetime.datetime, List[str], None]:
        """
        Convert string value to appropriate Python type based on field type.
        
        Args:
            value: String value from request parameter
            field: Django model field
            lookup: Lookup type (affects parsing for some types)
            
        Returns:
            Parsed value in appropriate Python type
        """
        try:
            # Get field type for type-specific parsing
            field_type = field.get_internal_type().lower()
            
            # Handle different field types
            if field_type in ['datetimefield', 'datefield']:
                return self._parse_date_value(value, field_type)
                
            elif field_type in [
                'integerfield', 'autofield', 'bigautofield', 
                'smallintegerfield', 'bigintegerfield', 
                'positivesmallintegerfield', 'positiveintegerfield'
            ]:
                return int(value)
                
            elif field_type in ['floatfield', 'decimalfield']:
                return Decimal(value)
                
            elif field_type == 'booleanfield':
                return value.lower() in ['true', '1', 'yes', 'y', 't']
                
            elif field_type in ['manytomanyfield', 'foreignkey']:
                if lookup == 'in' or ',' in value:
                    return value.split(',')
                    
            # Default: return as string
            return value
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing value '{value}' for field type {field_type}: {e}")
            return value

    def _parse_date_value(
        self, value: str, field_type: str
    ) -> Optional[Union[datetime.date, datetime.datetime]]:
        """
        Parse date or datetime string using multiple formats.
        
        Args:
            value: Date string to parse
            field_type: Field type ('datefield' or 'datetimefield')
            
        Returns:
            Parsed date or datetime object, or None if parsing fails
        """
        for fmt in self.date_formats:
            try:
                dt = datetime.datetime.strptime(value, fmt)
                # Return date only for date fields
                return dt.date() if field_type == 'datefield' else dt
            except ValueError:
                continue
        return None

    def build_filters(self) -> Q:
        """
        Construct a Q object from query parameters.
        
        This method processes all query parameters, validates them against model fields,
        and builds a complex filter expression.
        
        Returns:
            Django Q object representing all the filters
        """
        filters = Q()
        
        for param, value in self.request_params.items():
            # Skip pagination and special parameters
            if param in ['page', 'pageSize', 'ordering']:
                continue
                
            # Parse parameter into field name and lookup type
            if '__' in param:
                field_name, lookup = param.split('__', 1)
            else:
                field_name = param
                lookup = 'exact'
            
            # Get actual field name (handles camelCase/snake_case conversion)
            resolved_field_name = self._resolve_field_name(field_name)
            if not resolved_field_name:
                logger.debug(f"Skipping filter for unknown field: {field_name}")
                continue
                
            # Validate lookup type
            if lookup not in self.valid_lookups:
                logger.debug(f"Skipping invalid lookup type: {lookup}")
                continue
                
            # Get field object
            field = self.fields[resolved_field_name]
            
            # Parse value according to field type
            parsed_value = self._parse_value(value, field, lookup)
            if parsed_value is None:
                logger.debug(f"Skipping filter with unparseable value: {value}")
                continue

            # Handle special cases for different lookup types
            filter_expr = self._build_filter_expression(resolved_field_name, lookup, parsed_value)
            if filter_expr:
                filters &= filter_expr
                
        return filters
    
    def _build_filter_expression(
        self, field_name: str, lookup: str, value: Any
    ) -> Optional[Q]:
        """
        Build a filter expression for a specific field and lookup.
        
        Args:
            field_name: Field name to filter on
            lookup: Lookup type
            value: Parsed value to filter by
            
        Returns:
            Q object for the filter or None if invalid
        """
        # Handle range lookup
        if lookup == 'range' and isinstance(value, str):
            values = value.split(',')[:2]
            if len(values) == 2:
                return Q(**{f'{field_name}__range': values})
            return None
            
        # Handle 'in' lookup with list values
        elif lookup == 'in' and isinstance(value, list):
            return Q(**{f'{field_name}__in': value})
            
        # Handle boolean 'isnull' lookup
        elif lookup == 'isnull':
            bool_value = False
            if isinstance(value, bool):
                bool_value = value
            elif isinstance(value, str):
                bool_value = value.lower() in ['true', '1', 'yes', 'y', 't']
            return Q(**{f'{field_name}__isnull': bool_value})
            
        # Standard lookup
        else:
            return Q(**{f'{field_name}__{lookup}': value})
            
    def apply_to_queryset(self) -> QuerySet:
        """
        Apply the built filters directly to the queryset.
        
        This is a convenience method that builds and applies filters in one step.
        
        Returns:
            Filtered queryset
        """
        filters = self.build_filters()
        return self.queryset.filter(filters)