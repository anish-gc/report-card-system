import logging

from students.models import ReportCard, Mark, Student
from students.models.subject_model import Subject
from students.serializers.reportcard_serializer import (
    ReportCardWriteSerializer,
    ReportCardReadSerializer,
    ReportCardSummarySerializer,
    StudentYearPerformanceSerializer,
)
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView

logger = logging.getLogger("django")


class ReportCardCreateListApiView(BaseApiView):
    """
    Optimized API endpoint for report card operations.
    Handles N+1 query problems with proper prefetching.
    """
    db_table_name = 'report_cards'
    
    def get_optimized_queryset(self):
        """Get optimized queryset with proper prefetching to avoid N+1 queries."""
        return (
            ReportCard.objects
            .with_student_details()
            .with_marks()
            .with_aggregated_data()
        )
    
    def get(self, request):
        try:
            # Get query parameters for filtering
            year = request.query_params.get('year')
            term = request.query_params.get('term')
            student_id = request.query_params.get('student_id')
            detailed = request.query_params.get('detailed', 'false').lower() == 'true'
            # Start with optimized queryset
            queryset = self.get_optimized_queryset()
            
            # Apply filters
            if year:
                queryset = queryset.for_year(int(year))
            if term:
                queryset = queryset.for_term(term)
            if student_id:
                queryset = queryset.filter(student_id=int(student_id))
            
            # Choose serializer based on detailed parameter
            if detailed:
                serializer_class = ReportCardReadSerializer
            else:
                serializer_class = ReportCardSummarySerializer
                # For summary, we don't need marks prefetching
                queryset = ReportCard.objects.with_student_details()
                if year:
                    queryset = queryset.for_year(int(year))
                if term:
                    queryset = queryset.for_term(term)
                if student_id:
                    queryset = queryset.filter(student_id=int(student_id))
            
            report_cards = queryset.order_by('-year', '-term', 'student__name')
            serializer = serializer_class(report_cards, many=True)
            
            return self.handle_success(
                "Report cards retrieved successfully.",
                serializer.data
            )
            
        except ValueError as e:
            return self.handle_custom_api_exception(
                CustomAPIException(f"Invalid parameter value: {str(e)}")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)

    def post(self, request):
        try:
            serializer = ReportCardWriteSerializer(
                data=request.data,
                context={"request": request}
            )
            if serializer.is_valid():
                report_card = serializer.save()
                
                # Return the created report card with full details
                detailed_report_card = ReportCard.objects.get_detailed_report_card(
                    report_card.id
                )
                response_serializer = ReportCardReadSerializer(detailed_report_card)
                
                return self.handle_success(
                    "Report card created successfully.",
                    response_serializer.data
                )
            return self.handle_invalid_serializer(serializer)
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            print(exe)
            return self.handle_view_exception(exe)


class ReportCardDetailsApiView(BaseApiView):
    """
    Optimized API endpoint for report card detail operations.
    """
    db_table_name = 'report_cards'

    def get(self, request, pk):
        try:
            report_card = ReportCard.objects.get_detailed_report_card(pk)
            serializer = ReportCardReadSerializer(report_card)
            
            return self.handle_success(
                "Report card retrieved successfully.",
                serializer.data
            )
        except ReportCard.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Report card not found.")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)

    def patch(self, request, pk):
        try:
            report_card = ReportCard.objects.get(id=pk)
            serializer = ReportCardWriteSerializer(
                report_card,
                data=request.data,
                partial=True,
                context={"request": request}
            )
            if serializer.is_valid():
                updated_report_card = serializer.save()
                
                # Return updated report card with full details
                detailed_report_card = ReportCard.objects.get_detailed_report_card(
                    updated_report_card.id
                )
                response_serializer = ReportCardReadSerializer(detailed_report_card)
                
                return self.handle_success(
                    "Report card updated successfully.",
                    response_serializer.data
                )
            return self.handle_invalid_serializer(serializer)
        except ReportCard.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Report card not found.")
            )
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)

    def delete(self, request, pk):
        try:
            report_card = ReportCard.objects.get(id=pk)
            report_card.delete()
            return self.handle_success("Report card deleted successfully.")
        except ReportCard.DoesNotExist:
            return self.handle_custom_api_exception(
                CustomAPIException("Report card not found.")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)
        
class StudentPerformanceApiView(BaseApiView):
    """
    API endpoint for student performance analytics.
    Optimized for aggregation queries.
    """
    db_table_name = 'report_cards'

    def get(self, request, student_id):
        try:
            year = request.query_params.get('year')
            
            if not year:
                return self.handle_custom_api_exception(
                    CustomAPIException("Year parameter is required.")
                )
            
            # Check if student exists
            if not Student.objects.filter(id=student_id, is_active=True).exists():
                return self.handle_custom_api_exception(
                    CustomAPIException("Student not found or inactive.")
                )
            
            # Get student's report cards for the year
            report_cards = ReportCard.objects.get_student_report_cards(
                student_id, int(year)
            )
            
            # Get yearly performance summary
            performance_summary = ReportCard.objects.calculate_year_averages(
                student_id, int(year)
            )
            
            # Serialize data
            report_cards_serializer = ReportCardReadSerializer(report_cards, many=True)
            performance_serializer = StudentYearPerformanceSerializer(performance_summary)
            
            data = {
                'report_cards': report_cards_serializer.data,
                'performance_summary': performance_serializer.data
            }
            
            return self.handle_success(
                "Student performance retrieved successfully.",
                data
            )
            
        except ValueError as e:
            return self.handle_custom_api_exception(
                CustomAPIException(f"Invalid parameter value: {str(e)}")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)
