from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib import parse
from typing import Dict, Any, Optional, Union
import functools
from django.utils.encoding import force_str


class URLHelper:
    """
    Helper class for URL manipulation operations.
    
    This class provides utility methods for modifying query parameters in URLs.
    It's separated for better organization and potential reuse outside pagination.
    """
    
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def replace_query_param(url: str, key: str, val: str) -> str:
        """
        Replace or add a query parameter in a URL.
        
        This implementation is optimized with LRU caching to avoid 
        reprocessing the same URL modifications repeatedly.
        
        Args:
            url: The original URL
            key: Query parameter key
            val: New value for the parameter
            
        Returns:
            Modified URL with updated query parameter
        """
        (scheme, netloc, path, query, fragment) = parse.urlsplit(force_str(url))
        query_dict = parse.parse_qs(query, keep_blank_values=True)
        query_dict[force_str(key)] = [force_str(val)]
        query = parse.urlencode(sorted(query_dict.items()), doseq=True)
        return parse.urlunsplit((scheme, netloc, path, query, fragment))

    @staticmethod
    @functools.lru_cache(maxsize=128)
    def remove_query_param(url: str, key: str) -> str:
        """
        Remove a query parameter from a URL.
        
        This implementation is optimized with LRU caching to avoid 
        reprocessing the same URL modifications repeatedly.
        
        Args:
            url: The original URL
            key: Query parameter key to remove
            
        Returns:
            Modified URL with parameter removed
        """
        (scheme, netloc, path, query, fragment) = parse.urlsplit(force_str(url))
        query_dict = parse.parse_qs(query, keep_blank_values=True)
        query_dict.pop(key, None)
        query = parse.urlencode(sorted(query_dict.items()), doseq=True)
        return parse.urlunsplit((scheme, netloc, path, query, fragment))


class CustomPagination(PageNumberPagination):
    """
    Enhanced pagination class with advanced link generation.
    
    Features:
    - Configurable page sizes
    - First/last page navigation links
    - Consistent response format
    - Optimized URL manipulation
    
    Attributes:
        page_size: Default number of items per page
        page_size_query_param: Parameter name for page size in URL
        max_page_size: Maximum allowed page size
        page_query_param: Parameter name for page number in URL
    """
    page_size = 10
    page_size_query_param = 'pageSize'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """
        Return a paginated style Response object for the given output data.
        """
        return Response({
            'responseCode': "0",
            'message': "Success",
            'results': data,
            'count': self.page.paginator.count,
            'pageSize': self.get_page_size(self.request),
            'currentPage': self.page.number,
            'totalPages': self.page.paginator.num_pages,
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'first': self.get_first_link(),
                'last': self.get_last_link()
            },
        })
    
    def get_paginated_response_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override the default schema to include our custom pagination fields.
        
        This is important for automatic API documentation (like OpenAPI/Swagger).
        
        Args:
            schema: The schema for the paginated items
            
        Returns:
            Updated schema including pagination fields with examples
        """
        return {
            'type': 'object',
            'required': ['count', 'pageSize', 'currentPage', 'totalPages', 'links', 'results'],
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': 'Total number of items matching the query',
                    'example': 100,
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'Number of items per page',
                    'example': 10,
                },
                'currentPage': {
                    'type': 'integer',
                    'description': 'Current page number',
                    'example': 1,
                },
                'totalPages': {
                    'type': 'integer',
                    'description': 'Total number of pages',
                    'example': 10,
                },
                'links': {
                    'type': 'object',
                    'required': ['next', 'previous', 'first', 'last'],
                    'properties': {
                        'next': {
                            'type': 'string',
                            'format': 'uri',
                            'nullable': True,
                            'description': 'URL to the next page',
                            'example': 'http://api.example.org/accounts/?page=2',
                        },
                        'previous': {
                            'type': 'string',
                            'format': 'uri',
                            'nullable': True,
                            'description': 'URL to the previous page',
                            'example': None,
                        },
                        'first': {
                            'type': 'string',
                            'format': 'uri',
                            'nullable': False,
                            'description': 'URL to the first page',
                            'example': 'http://api.example.org/accounts/?page=1',
                        },
                        'last': {
                            'type': 'string',
                            'format': 'uri',
                            'nullable': False,
                            'description': 'URL to the last page',
                            'example': 'http://api.example.org/accounts/?page=10',
                        },
                    },
                    'example': {
                        'next': 'http://api.example.org/accounts/?page=2',
                        'previous': None,
                        'first': 'http://api.example.org/accounts/?page=1',
                        'last': 'http://api.example.org/accounts/?page=10'
                    }
                },
                'results': schema,
            },
            'example': {
                'count': 100,
                'pageSize': 10,
                'currentPage': 1,
                'totalPages': 10,
                'links': {
                    'next': 'http://api.example.org/accounts/?page=2',
                    'previous': None,
                    'first': 'http://api.example.org/accounts/?page=1',
                    'last': 'http://api.example.org/accounts/?page=10'
                },
                'results': []
            }
        }

    def get_first_link(self) -> Optional[str]:
        """
        Get URL for the first page.
        
        Returns:
            URL with page parameter set to 1 or removed
        """
        if not self.page.paginator.num_pages:
            return None
            
        url = self.request.build_absolute_uri()
        return URLHelper.replace_query_param(url, self.page_query_param, 1)

    def get_last_link(self) -> Optional[str]:
        """
        Get URL for the last page.
        
        Returns:
            URL with page parameter set to the last page number
        """
        if not self.page.paginator.num_pages:
            return None
            
        url = self.request.build_absolute_uri()
        page_number = self.page.paginator.num_pages
        return URLHelper.replace_query_param(url, self.page_query_param, page_number)