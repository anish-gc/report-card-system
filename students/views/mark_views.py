import logging

from students.models import ReportCard, Mark
from students.models.subject_model import Subject
from students.serializers.mark_serializer import MarkReadSerializer
from students.serializers.reportcard_serializer import (
    MarkWriteSerializer,
    SubjectPerformanceSerializer,
)
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView

logger = logging.getLogger("django")


class MarkCreateListApiView(BaseApiView):
    """
    Optimized API endpoint for mark operations.
    """

    db_table_name = "marks"

    def get_optimized_queryset(self):
        """Get optimized queryset with proper prefetching."""
        return Mark.objects.with_report_card_details().with_subject_details()

    def get(self, request):
        try:
            # Get query parameters for filtering
            report_card_id = request.query_params.get("report_card_id")
            subject_id = request.query_params.get("subject_id")
            student_id = request.query_params.get("student_id")
            year = request.query_params.get("year")
            term = request.query_params.get("term")

            queryset = self.get_optimized_queryset()

            # Apply filters
            if report_card_id:
                queryset = queryset.filter(report_card_id=int(report_card_id))
            if subject_id:
                queryset = queryset.for_subject(int(subject_id))
            if student_id:
                queryset = queryset.for_student(int(student_id))
            if year:
                queryset = queryset.for_year(int(year))
            if term:
                queryset = queryset.for_term(term)

            marks = queryset.order_by("report_card", "subject__code")
            serializer = MarkReadSerializer(marks, many=True)

            return self.handle_success("Marks retrieved successfully.", serializer.data)

        except ValueError as e:
            return self.handle_custom_api_exception(
                CustomAPIException(f"Invalid parameter value: {str(e)}")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)

    def post(self, request):
        try:
            serializer = MarkWriteSerializer(
                data=request.data, context={"request": request}
            )
            if serializer.is_valid():
                mark = serializer.save()

                # Update report card aggregates
                Mark.objects.update_report_card_aggregates(mark.report_card)

                # Return the created mark with full details
                detailed_mark = (
                    Mark.objects.with_report_card_details()
                    .with_subject_details()
                    .get(id=mark.id)
                )
                response_serializer = MarkReadSerializer(detailed_mark)

                return self.handle_success(
                    "Mark created successfully.", response_serializer.data
                )
            return self.handle_invalid_serializer(serializer)
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)


class MarkDetailsApiView(BaseApiView):
    """
    Optimized API endpoint for mark detail operations.
    """

    db_table_name = "marks"

    def get(self, request, pk):
        try:
            mark = (
                Mark.objects.with_report_card_details()
                .with_subject_details()
                .get(id=pk)
            )
         
            serializer = MarkReadSerializer(mark)
            return self.handle_success("Mark retrieved successfully.", serializer.data)
        except Mark.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Mark not found.")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)

    def patch(self, request, pk):
        try:
            mark = Mark.objects.get(id=pk)
            serializer = MarkWriteSerializer(
                mark, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                updated_mark = serializer.save()

                # Update report card aggregates
                Mark.objects.update_report_card_aggregates(updated_mark.report_card)

                # Return updated mark with full details
                detailed_mark = (
                    Mark.objects.with_report_card_details()
                    .with_subject_details()
                    .get(id=updated_mark.id)
                )
                response_serializer = MarkReadSerializer(detailed_mark)

                return self.handle_success(
                    "Mark updated successfully.", response_serializer.data
                )
            return self.handle_invalid_serializer(serializer)
        except Mark.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Mark not found.")
            )
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def delete(self, request, pk):
        try:
            mark = Mark.objects.get(id=pk)
            report_card = mark.report_card
            mark.delete()

            # Update report card aggregates after deletion
            Mark.objects.update_report_card_aggregates(report_card)

            return self.handle_success("Mark deleted successfully.")
        except Mark.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Mark not found.")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)


class SubjectPerformanceApiView(BaseApiView):
    """
    API endpoint for subject performance analytics.
    """

    db_table_name = "marks"

    def get(self, request, subject_id):
        try:
            year = request.query_params.get("year")

            # Check if subject exists
            if not Subject.objects.filter(id=subject_id, is_active=True).exists():
                return self.handle_custom_api_exception(
                    CustomAPIException("Subject not found or inactive.")
                )

            # Get subject performance statistics
            performance_data = Mark.objects.get_subject_performance(
                subject_id, int(year) if year else None
            )

            serializer = SubjectPerformanceSerializer(performance_data)

            return self.handle_success(
                "Subject performance retrieved successfully.", serializer.data
            )

        except ValueError as e:
            return self.handle_custom_api_exception(
                CustomAPIException(f"Invalid parameter value: {str(e)}")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)


class BulkMarkCreateApiView(BaseApiView):
    """
    Optimized API endpoint for bulk mark creation.
    Handles multiple marks for a report card efficiently.
    """

    db_table_name = "marks"

    def post(self, request):
        try:
            report_card_id = request.data.get("report_card_id")
            marks_data = request.data.get("marks", [])

            if not report_card_id:
                return self.handle_custom_api_exception(
                    CustomAPIException("Report card ID is required.")
                )

            if not marks_data:
                return self.handle_custom_api_exception(
                    CustomAPIException("Marks data is required.")
                )

            # Get report card
            try:
                report_card = ReportCard.objects.get(id=report_card_id)
            except ReportCard.DoesNotExist:
                return self.handle_custom_api_exception(
                    CustomAPIException("Report card not found.")
                )

            # Validate marks data
            serializer = MarkWriteSerializer(data=marks_data, many=True)
            if not serializer.is_valid():
                return self.handle_invalid_serializer(serializer)

            # Bulk create marks
            created_marks = Mark.objects.bulk_create_marks(
                report_card, serializer.validated_data
            )

            # Update report card aggregates
            Mark.objects.update_report_card_aggregates(report_card)

            return self.handle_success(
                f"Successfully created {len(created_marks)} marks.",
                {"created_count": len(created_marks)},
            )

        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)
