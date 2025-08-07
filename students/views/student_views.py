import logging
from students.models.student_model import Student
from students.serializers.student_serializer import StudentReadSerializer, StudentSerializer
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView
from datetime import datetime

logger = logging.getLogger("django")


class StudentCreateListApiView(BaseApiView):
    """
    API endpoint for retrieving a list of students.
    Retrieves all students that are not deleted.
    """
    db_table_name = 'students'
    def get(self, request):
        try:
            return self.handle_serializer_data(Student, StudentReadSerializer, True)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def post(self, request):
        try:
            serializer = StudentSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return self.handle_success("student created successfully.")

            return self.handle_invalid_serializer(serializer)

        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)

        except Exception as exe:
            return self.handle_view_exception(exe)


class StudentDetailsApiView(BaseApiView):
    """
    API endpoint for updating an existing student.
    Allows modification of an existing student's attributes.
    """
    db_table_name = 'students'

    def get(self, request, pk):
        try:
            return self.handle_serializer_data(
                Student, StudentReadSerializer, False, id=pk
            )

        except Exception as exe:
            return self.handle_view_exception(exe)

    def patch(self, request, pk):
        try:
            student = Student.objects.get(id=pk)

            serializer = StudentSerializer(
                student, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return self.handle_success("Student updated successfully.")

            return self.handle_invalid_serializer(serializer)

        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def delete(self, request, pk):
        try:
            student = Student.objects.get(id=pk)
            student.delete()

            return self.handle_success("student deleted successfully.")

        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)
