from rest_framework.views import APIView

from utilities.custom_authentication_class import CustomAuthentication
from utilities.custom_permission_class import CustomPermission
from utilities.custom_response_class import HandleResponseMixin 


class BaseAPIView(APIView, HandleResponseMixin):
    """
    Base class for API views.
    """
  
    authentication_classes = [CustomAuthentication]
    permission_classes = [CustomPermission]

