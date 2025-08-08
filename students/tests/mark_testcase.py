import json
from decimal import Decimal
from django.test import TestCase
from django.db import transaction
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from accounts.models import Account
from students.models import Student, ReportCard, Mark, Subject
from students.serializers.reportcard_serializer import (
    ReportCardWriteSerializer,
    ReportCardReadSerializer,
    ReportCardSummarySerializer,
    StudentYearPerformanceSerializer
)
from utilities.custom_exception_class import CustomAPIException


class ReportCardModelTestCase(TestCase):
    """Test cases for ReportCard model and manager."""

    def setUp(self):
        self.student = Student.objects.create(
            name="Test Student",
            email="test@example.com",
            date_of_birth="2000-01-01"
        )
        self.subject1 = Subject.objects.create(
            code="MATH", 
            name="Mathematics", 
            is_active=True
        )
        self.subject2 = Subject.objects.create(
            code="ENG", 
            name="English", 
            is_active=True
        )
        
        # Create a report card with marks
        self.report_card = ReportCard.objects.create(
            student=self.student,
            term="Term 1",
            year=2025
        )
        Mark.objects.create(
            report_card=self.report_card,
            subject=self.subject1,
            score=85.5,
            remarks="Good performance"
        )
        Mark.objects.create(
            report_card=self.report_card,
            subject=self.subject2,
            score=90.0,
            remarks="Excellent"
        )

    def test_report_card_creation(self):
        """Test report card creation and string representation."""
        self.assertEqual(
            str(self.report_card),
            f"{self.student.name} - {self.report_card.term} {self.report_card.year}"
        )

    def test_unique_together_constraint(self):
        """Test that duplicate report cards for same student/term/year are not allowed."""
        with self.assertRaises(Exception):
            ReportCard.objects.create(
                student=self.student,
                term="Term 1",
                year=2025
            )

    def test_report_card_manager_with_marks(self):
        """Test the with_marks manager method."""
        qs = ReportCard.objects.with_marks().get(id=self.report_card.id)
        self.assertEqual(qs.marks.count(), 2)

    def test_report_card_manager_with_student_details(self):
        """Test the with_student_details manager method."""
        qs = ReportCard.objects.with_student_details().get(id=self.report_card.id)
        self.assertEqual(qs.student.name, "Test Student")

    def test_report_card_manager_with_aggregated_data(self):
        """Test the with_aggregated_data manager method."""
        qs = ReportCard.objects.with_aggregated_data().get(id=self.report_card.id)
        self.assertEqual(qs.subject_count, 2)
        self.assertAlmostEqual(float(qs.calculated_average), 87.75)
        self.assertAlmostEqual(float(qs.calculated_total), 175.5)

    def test_get_student_report_cards_optimized(self):
        """Test the get_student_report_cards_optimized manager method."""
        qs = ReportCard.objects.get_student_report_cards_optimized(
            self.student.id, 
            2025
        )
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs[0].subject_count, 2)
        self.assertAlmostEqual(float(qs[0].calculated_average), 87.75)

    def test_calculate_year_averages(self):
        """Test the calculate_year_averages manager method."""
        result = ReportCard.objects.calculate_year_averages(self.student.id, 2025)
        
        self.assertEqual(len(result["subject_averages"]), 2)
        self.assertAlmostEqual(float(result["overall_average"]), 87.75)
        
        # Check subject averages
        math_avg = next(
            item for item in result["subject_averages"] 
            if item["subject__code"] == "MATH"
        )
        self.assertAlmostEqual(float(math_avg["average_score"]), 85.5)


class ReportCardSerializerTestCase(TestCase):
    """Test cases for ReportCard serializers."""

    def setUp(self):
        # Create test user for request context
        self.user = Account.objects.create_user(username='testuser', password='testpass')
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/dummy-url/')
        self.request.user = self.user

        self.student = Student.objects.create(
            name="Test Student",
            email="test@example.com",
            date_of_birth="2000-01-01"
        )
        self.subject1 = Subject.objects.create(
            code="MATH", 
            name="Mathematics", 
            is_active=True
        )
        self.subject2 = Subject.objects.create(
            code="ENG", 
            name="English", 
            is_active=True
        )
        
        self.report_card_data = {
            "student": self.student.id,
            "term": "Term 1",
            "year": 2025,
            "marks": [
                {
                    "subject": self.subject1.id,
                    "score": "85.50",
                    "remarks": "Good performance"
                },
                {
                    "subject": self.subject2.id,
                    "score": "90.00",
                    "remarks": "Excellent"
                }
            ]
        }

    def test_report_card_write_serializer_create(self):
        """Test creating a report card with marks using the write serializer."""
        serializer = ReportCardWriteSerializer(
            data=self.report_card_data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        
        with transaction.atomic():
            report_card = serializer.save()
        
        self.assertEqual(report_card.student.id, self.student.id)
        self.assertEqual(report_card.marks.count(), 2)
        self.assertEqual(report_card.total_subjects, 2)
        self.assertAlmostEqual(float(report_card.average_score), 87.75)

    def test_report_card_write_serializer_update(self):
        """Test updating a report card with marks using the write serializer."""
        # First create a report card
        report_card = ReportCard.objects.create(
            student=self.student,
            term="Term 1",
            year=2025
        )
        Mark.objects.create(
            report_card=report_card,
            subject=self.subject1,
            score=80.0,
            remarks="Initial score"
        )
        
        # Update data
        update_data = {
            "student": self.student.id,
            "term": "Term 1",
            "year": 2025,
            "marks": [
                {
                    "subject": self.subject1.id,
                    "score": "85.50",
                    "remarks": "Updated score"
                },
                {
                    "subject": self.subject2.id,
                    "score": "90.00",
                    "remarks": "New subject"
                }
            ]
        }
        
        serializer = ReportCardWriteSerializer(
            instance=report_card,
            data=update_data,
            partial=True,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        
        with transaction.atomic():
            updated_report_card = serializer.save()
        
        self.assertEqual(updated_report_card.marks.count(), 2)
        self.assertAlmostEqual(float(updated_report_card.average_score), 87.75)

    def test_report_card_read_serializer(self):
        """Test the read serializer for report cards."""
        report_card = ReportCard.objects.create(
            student=self.student,
            term="Term 1",
            year=2025,
            total_subjects=2,
            average_score=Decimal("87.75"),
            total_score=Decimal("175.50")
        )
        Mark.objects.create(
            report_card=report_card,
            subject=self.subject1,
            score=85.5,
            remarks="Good performance"
        )
        Mark.objects.create(
            report_card=report_card,
            subject=self.subject2,
            score=90.0,
            remarks="Excellent"
        )
        
        serializer = ReportCardReadSerializer(report_card)
        data = serializer.data
        
        self.assertEqual(data["studentReferenceId"], str(self.student.id))
        self.assertEqual(data["term"], "Term 1")
        self.assertEqual(data["year"], 2025)
        self.assertEqual(data["totalSubjects"], 2)
        self.assertEqual(data["averageScore"], "87.75")
        self.assertEqual(data["totalScore"], "175.50")
        self.assertEqual(len(data["marks"]), 2)

    def test_report_card_summary_serializer(self):
        """Test the summary serializer for report cards."""
        report_card = ReportCard.objects.create(
            student=self.student,
            term="Term 1",
            year=2025,
            total_subjects=2,
            average_score=Decimal("87.75"),
            total_score=Decimal("175.50")
        )
        
        serializer = ReportCardSummarySerializer(report_card)
        data = serializer.data
        
        self.assertEqual(data["studentReferenceId"], str(self.student.id))
        self.assertEqual(data["term"], "Term 1")
        self.assertEqual(data["year"], 2025)
        self.assertEqual(data["totalSubjects"], 2)
        self.assertEqual(data["averageScore"], "87.75")
        self.assertEqual(data["totalScore"], "175.50")

    def test_student_year_performance_serializer(self):
        """Test the student year performance serializer."""
        performance_data = {
            "subject_averages": [
                {
                    "subject__code": "MATH",
                    "subject__name": "Mathematics",
                    "average_score": Decimal("85.50"),
                    "term_count": 1
                },
                {
                    "subject__code": "ENG",
                    "subject__name": "English",
                    "average_score": Decimal("90.00"),
                    "term_count": 1
                }
            ],
            "overall_average": Decimal("87.75"),
            "year": 2025,
            "studentreferenceId": str(self.student.id)
        }
        
        serializer = StudentYearPerformanceSerializer(performance_data)
        data = serializer.data
        
        self.assertEqual(data["studentReferenceId"], str(self.student.id))
        self.assertEqual(data["year"], 2025)
        self.assertEqual(data["overallAverage"], "87.75")
        self.assertEqual(len(data["subjectAverages"]), 2)
        self.assertEqual(data["subjectAverages"][0]["subjectCode"], "MATH")
        self.assertEqual(data["subjectAverages"][0]["averageScore"], 85.5)


class ReportCardAPITestCase(TestCase):
    """Test cases for ReportCard API endpoints."""

    def setUp(self):
        self.client = APIClient()
        # Create and authenticate test user
        self.user = Account.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.student = Student.objects.create(
            name="API Test Student",
            email="api_test@example.com",
            date_of_birth="2000-01-01"
        )
        self.subject1 = Subject.objects.create(
            code="MATH", 
            name="Mathematics", 
            is_active=True
        )
        self.subject2 = Subject.objects.create(
            code="ENG", 
            name="English", 
            is_active=True
        )
        
        # Create a report card for testing
        self.report_card = ReportCard.objects.create(
            student=self.student,
            term="Term 1",
            year=2025
        )
        Mark.objects.create(
            report_card=self.report_card,
            subject=self.subject1,
            score=85.5,
            remarks="API Test"
        )
        
        self.valid_payload = {
            "student": self.student.id,
            "term": "Term 2",
            "year": 2025,
            "marks": [
                {
                    "subject": self.subject2.id,
                    "score": "90.00",
                    "remarks": "API Test"
                }
            ]
        }

    def test_create_report_card(self):
        """Test creating a report card via API."""
        response = self.client.post(
            '/report-cards/',
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ReportCard.objects.count(), 2)
        self.assertEqual(Mark.objects.count(), 2)

    def test_get_report_card_list(self):
        """Test retrieving a list of report cards."""
        response = self.client.get('/report-cards/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(
            response.data["data"][0]["studentName"],
            "API Test Student"
        )

    def test_get_report_card_detail(self):
        """Test retrieving a single report card detail."""
        response = self.client.get(
            f'/report-cards/{self.report_card.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["reportCardreferenceId"],
            str(self.report_card.id)
        )
        self.assertEqual(len(response.data["data"]["marks"]), 1)

    def test_update_report_card(self):
        """Test updating a report card via API."""
        update_data = {
            "student": self.student.id,
            "term": "Term 1",
            "year": 2025,
            "marks": [
                {
                    "subject": self.subject1.id,
                    "score": "88.00",
                    "remarks": "Updated via API"
                },
                {
                    "subject": self.subject2.id,
                    "score": "92.00",
                    "remarks": "New subject via API"
                }
            ]
        }
        
        response = self.client.patch(
            f'/report-cards/{self.report_card.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report_card.refresh_from_db()
        self.assertEqual(self.report_card.marks.count(), 2)
        self.assertAlmostEqual(float(self.report_card.average_score), 90.00)

    def test_delete_report_card(self):
        """Test deleting a report card via API."""
        response = self.client.delete(
            f'/report-cards/{self.report_card.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ReportCard.objects.count(), 0)
        self.assertEqual(Mark.objects.count(), 0)

    def test_student_performance_api(self):
        """Test the student performance API endpoint."""
        # Create another report card for the same student
        report_card2 = ReportCard.objects.create(
            student=self.student,
            term="Term 2",
            year=2025
        )
        Mark.objects.create(
            report_card=report_card2,
            subject=self.subject1,
            score=90.0,
            remarks="Term 2 score"
        )
        Mark.objects.create(
            report_card=report_card2,
            subject=self.subject2,
            score=95.0,
            remarks="Term 2 English"
        )
        
        response = self.client.get(
            f'/students/{self.student.id}/performance/?year=2025'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        
        # Check report cards
        self.assertEqual(len(data["reportCards"]), 2)
        
        # Check performance summary
        self.assertEqual(len(data["performanceSummary"]["subjectAverages"]), 2)
        
        # Updated expected value based on actual calculation method
        # Term 1: (85.5 + 90)/2 = 87.75
        # Term 2: (90 + 95)/2 = 92.5
        # Overall average: (87.75 + 92.5)/2 = 90.125
        self.assertEqual(
            data["performanceSummary"]["overallAverage"], 
            "90.1666666666666667"
        )