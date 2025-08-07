import logging
from students.models.subject_model import Subject
from students.serializers.subject_serializer import SubjectReadSerializer, SubjectSerializer
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView

logger = logging.getLogger("django")

class SubjectCreateListApiView(BaseApiView):
    """
    API endpoint for subject operations
    """
    db_table_name = 'subjects'
    
    def get(self, request):
        try:
            return self.handle_serializer_data(Subject, SubjectReadSerializer, True)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def post(self, request):
        try:
            serializer = SubjectSerializer(
                data=request.data, 
                context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return self.handle_success("Subject created successfully.")
            return self.handle_invalid_serializer(serializer)
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)

class SubjectDetailsApiView(BaseApiView):
    """
    API endpoint for subject detail operations
    """
    db_table_name = 'subjects'

    def get(self, request, pk):
        try:
            return self.handle_serializer_data(
                Subject, SubjectReadSerializer, False, id=pk
            )
        except Exception as exe:
            return self.handle_view_exception(exe)

    def patch(self, request, pk):
        try:
            subject = Subject.objects.get(id=pk)
            serializer = SubjectSerializer(
                subject, 
                data=request.data, 
                partial=True, 
                context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return self.handle_success("Subject updated successfully.")
            return self.handle_invalid_serializer(serializer)
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def delete(self, request, pk):
        try:
            subject = Subject.objects.get(id=pk)
            subject.delete()
            return self.handle_success("Subject deleted successfully.")
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)