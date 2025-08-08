import logging

from students.models import ReportCard, Mark, Student
from students.serializers.reportcard_serializer import (
    ReportCardWriteSerializer,
    ReportCardReadSerializer,
    ReportCardSummarySerializer,
    StudentYearPerformanceSerializer,
)
from students.tasks import (
    calculate_report_card_aggregates,
    calculate_student_grade,
    calculate_class_averages
)
from utilities.custom_exception_class import CustomAPIException
from utilities.custom_permission_class import BaseApiView

logger = logging.getLogger("django")


class ReportCardCreateListApiView(BaseApiView):
    """
    Optimized API endpoint for report card operations with async calculations.
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
            
            # Check for class averages request
            calculate_class_stats = request.query_params.get('include_class_stats', 'false').lower() == 'true'
            
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
            
            response_data = {
                'report_cards': serializer.data
            }
            
            # Trigger class averages calculation if requested
            if calculate_class_stats and year:
                task = calculate_class_averages.apply_async(
                    args=[int(year), term],
                    queue='calculations'
                )
                response_data['class_stats_task_id'] = task.id
            
            return self.handle_success(
                "Report cards retrieved successfully.",
                response_data
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
                # Mark as calculating
                report_card = serializer.save()
                report_card.calculation_status = 'calculating'
                report_card.save(update_fields=['calculation_status'])
                
                # Trigger async calculation
                task = calculate_report_card_aggregates.apply_async(
                    args=[str(report_card.id)],
                    queue='calculations'
                )
                
                # Return the created report card with task info 
                detailed_report_card = ReportCard.objects.get_detailed_report_card(
                    report_card.id
                )
                response_serializer = ReportCardReadSerializer(detailed_report_card)
                
                response_data = response_serializer.data
                response_data['calculationTaskId'] = task.id
                response_data['calculationStatus'] = 'calculating'
                
                return self.handle_success(
                    "Report card created successfully. Calculations are being processed in the background.",
                    response_data
                )
            return self.handle_invalid_serializer(serializer)
        except CustomAPIException as exe:
            return self.handle_custom_api_exception(exe)
        except Exception as exe:
            return self.handle_view_exception(exe)


class ReportCardDetailsApiView(BaseApiView):
    """
    Optimized API endpoint for report card detail operations with calculation status.
    """
    db_table_name = 'report_cards'

    def get(self, request, pk):
        try:
            report_card = ReportCard.objects.get_detailed_report_card(pk)
            
            # Check if calculations are needed
            needs_calc = report_card.needs_calculation()
            task_id = None
            
            if needs_calc:
                # Trigger background calculation
                task = calculate_report_card_aggregates.apply_async(
                    args=[str(pk)],
                    queue='calculations'
                )
                task_id = task.id
                
                # Update status
                report_card.calculation_status = 'calculating'
                report_card.save(update_fields=['calculation_status'])
            
            serializer = ReportCardReadSerializer(report_card)
            response_data = serializer.data
            
            if task_id:
                response_data['calculationTaskId'] = task_id
                response_data['message'] = "Calculations are being updated in the background."
            
            return self.handle_success(
                "Report card retrieved successfully.",
                response_data
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
                
                # Mark for recalculation
                updated_report_card.calculation_status = 'calculating'
                updated_report_card.save(update_fields=['calculation_status'])
                
                # Trigger async calculation
                task = calculate_report_card_aggregates.apply_async(
                    args=[str(updated_report_card.id)],
                    queue='calculations'
                )
                
                # Return updated report card with task info
                detailed_report_card = ReportCard.objects.get_detailed_report_card(
                    updated_report_card.id
                )
                response_serializer = ReportCardReadSerializer(detailed_report_card)
                
                response_data = response_serializer.data
                response_data['calculationTaskId'] = task.id
                
                return self.handle_success(
                    "Report card updated successfully. Calculations are being processed in the background.",
                    response_data
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


class StudentPerformanceApiView(BaseApiView):
    """
    API endpoint for student performance analytics with background calculation.
    """
    db_table_name = 'report_cards'

    def get(self, request, pk):
        try:
            year = request.query_params.get('year')
            
            if not year:
                return self.handle_custom_api_exception(
                    CustomAPIException("Year parameter is required.")
                )
            
            # Check if student exists
            if not Student.objects.filter(id=pk, is_active=True).exists():
                return self.handle_custom_api_exception(
                    CustomAPIException("Student not found or inactive.")
                )
            
            # Get student's report cards for the year with calculated fields
            report_cards = ReportCard.objects.get_student_report_cards_optimized(
                pk, int(year)
            )
            
            # Trigger background calculation for student performance
            performance_task = calculate_student_grade.apply_async(
                args=[str(pk), int(year)],
                queue='calculations'
            )
            
            # Get immediate performance summary (might be cached)
            performance_summary = ReportCard.objects.calculate_year_averages(
                pk, int(year)
            )
            
            # Check which report cards need calculation updates
            cards_needing_calc = []
            for card in report_cards:
                if card.needs_calculation():
                    task = calculate_report_card_aggregates.apply_async(
                        args=[str(card.id)],
                        queue='calculations'
                    )
                    cards_needing_calc.append({
                        'reporCardId': str(card.id),
                        'taskId': task.id
                    })
            
            # Serialize data with camelCase conversion
            report_cards_serializer = ReportCardReadSerializer(report_cards, many=True)
            performance_serializer = StudentYearPerformanceSerializer(performance_summary)
            
            data = {
                'reportCards': report_cards_serializer.data,
                'performanceSummary': performance_serializer.data,
                'backgroundTasks': {
                    'performance_calculation_task_id': performance_task.id,
                    'report_cards_being_calculated': cards_needing_calc
                }
            }
            
            message = "Student performance retrieved successfully."
            if cards_needing_calc or performance_task:
                message += " Some calculations are being updated in the background."
            
            return self.handle_success(message, data)
            
        except ValueError as e:
            return self.handle_custom_api_exception(
                CustomAPIException(f"Invalid parameter value: {str(e)}")
            )
        except Exception as exe:
            return self.handle_view_exception(exe)


class TaskStatusApiView(BaseApiView):
    """
    API endpoint to check the status of background calculation tasks.
    """
    
    def get(self, request, task_id):
        try:
            from celery.result import AsyncResult
            from django.conf import settings
            
            # Get task result
            result = AsyncResult(task_id)
            
            response_data = {
                'task_id': task_id,
                'status': result.status,
                'ready': result.ready(),
            }
            
            if result.ready():
                if result.successful():
                    response_data['result'] = result.result
                else:
                    response_data['error'] = str(result.info)
            else:
                # Task is still running
                response_data['info'] = result.info
            
            return self.handle_success(
                f"Task status retrieved successfully.",
                response_data
            )
            
        except Exception as exe:
            return self.handle_view_exception(exe)


class BulkCalculateApiView(BaseApiView):
    """
    API endpoint for triggering bulk calculations.
    """
    
    def post(self, request):
        try:
            # Get parameters
            year = request.data.get('year')
            term = request.data.get('term')
            student_ids = request.data.get('student_ids', [])
            report_card_ids = request.data.get('report_card_ids', [])
            
            tasks_queued = []
            
            # If specific report card IDs provided
            if report_card_ids:
                from students.tasks import bulk_calculate_report_cards
                task = bulk_calculate_report_cards.apply_async(
                    args=[report_card_ids],
                    queue='bulk_operations'
                )
                tasks_queued.append({
                    'type': 'bulk_report_cards',
                    'task_id': task.id,
                    'count': len(report_card_ids)
                })
            
            # If year-based calculation requested
            elif year:
                # Get report cards to calculate
                queryset = ReportCard.objects.filter(year=int(year), is_active=True)
                if term:
                    queryset = queryset.filter(term=term)
                if student_ids:
                    queryset = queryset.filter(student_id__in=student_ids)
                
                rc_ids = list(queryset.values_list('id', flat=True))
                
                if rc_ids:
                    from students.tasks import bulk_calculate_report_cards
                    task = bulk_calculate_report_cards.apply_async(
                        args=[rc_ids],
                        queue='bulk_operations'
                    )
                    tasks_queued.append({
                        'type': 'bulk_year_calculation',
                        'task_id': task.id,
                        'year': year,
                        'term': term,
                        'count': len(rc_ids)
                    })
                
                # Also calculate class averages
                class_task = calculate_class_averages.apply_async(
                    args=[int(year), term],
                    queue='calculations'
                )
                tasks_queued.append({
                    'type': 'class_averages',
                    'task_id': class_task.id,
                    'year': year,
                    'term': term
                })
            
            else:
                return self.handle_custom_api_exception(
                    CustomAPIException("Either year or report_card_ids must be provided.")
                )
            
            return self.handle_success(
                f"Successfully queued {len(tasks_queued)} calculation tasks.",
                {'tasks': tasks_queued}
            )
            
        except Exception as exe:
            return self.handle_view_exception(exe)
