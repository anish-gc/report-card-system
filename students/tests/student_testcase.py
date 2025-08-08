"""
Test cases for Student model, views, and serializers.
"""

import json
from datetime import date, timedelta
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.db import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from accounts.models import Account
from students.models.student_model import Student
from students.serializers.student_serializer import StudentSerializer, StudentReadSerializer
from utilities.custom_exception_class import CustomAPIException


class StudentModelTestCase(TestCase):
    """Test cases for Student model."""
    
    def setUp(self):
        """Set up test data."""
        self.valid_student_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'date_of_birth': date(1995, 5, 15)
        }
    
    def test_create_student_success(self):
        """Test successful student creation."""
        student = Student.objects.create(**self.valid_student_data)
        
        self.assertEqual(student.name, 'John Doe')
        self.assertEqual(student.email, 'john.doe@example.com')
        self.assertEqual(student.date_of_birth, date(1995, 5, 15))
        self.assertTrue(student.is_active)
        self.assertIsNotNone(student.id)
    
    def test_student_str_method(self):
        """Test student string representation."""
        student = Student.objects.create(**self.valid_student_data)
        expected_str = f"{student.name} ({student.email})"
        self.assertEqual(str(student), expected_str)
    
    def test_unique_email_constraint(self):
        """Test that email must be unique."""
        Student.objects.create(**self.valid_student_data)
        
        duplicate_data = self.valid_student_data.copy()
        duplicate_data['name'] = 'Jane Doe'
        
        with self.assertRaises(IntegrityError):
            Student.objects.create(**duplicate_data)
    
    def test_model_meta_attributes(self):
        """Test model meta attributes."""
        self.assertEqual(Student._meta.db_table, 'students')
        self.assertEqual(Student._meta.verbose_name, 'Student')
        self.assertEqual(Student._meta.verbose_name_plural, 'Students')
        self.assertEqual(Student._meta.ordering, ['name'])
    
    def test_model_indexes(self):
        """Test that proper indexes are created."""
        indexes = Student._meta.indexes
        self.assertEqual(len(indexes), 2)
        
        index_fields = [tuple(idx.fields) for idx in indexes]
        self.assertIn(('name', 'is_active'), index_fields)
        self.assertIn(('email', 'is_active'), index_fields)


class StudentSerializerTestCase(TestCase):
    """Test cases for Student serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = Account.objects.create_user(
            username='testuser',
            password='testpass',
        )
        self.request = RequestFactory().post('/')
        self.request.user = self.user
        self.valid_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'dateOfBirth': '1995-05-15',
            'isActive': True
        }
        
        self.student = Student.objects.create(
            name='Jane Smith',
            email='jane.smith@example.com',
            date_of_birth=date(1990, 1, 1),
            created_by=self.user
        )
    
    def test_student_serializer_valid_data(self):
        """Test StudentSerializer with valid data."""
        serializer = StudentSerializer(data=self.valid_data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['name'], 'John Doe')
        self.assertEqual(validated_data['email'], 'john.doe@example.com')
        self.assertEqual(validated_data['date_of_birth'], date(1995, 5, 15))
    
    def test_student_serializer_create(self):
        """Test creating student through serializer."""
        serializer = StudentSerializer(data=self.valid_data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        
        student = serializer.save()
        self.assertIsInstance(student, Student)
        self.assertEqual(student.name, 'John Doe')
        self.assertEqual(student.email, 'john.doe@example.com')
    
    def test_student_serializer_update(self):
        """Test updating student through serializer."""
        update_data = {
            'name': 'Jane Updated',
            'email': 'jane.updated@example.com'
        }
        
        serializer = StudentSerializer(
            self.student, 
            data=update_data, 
            partial=True,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        
        updated_student = serializer.save()
        self.assertEqual(updated_student.name, 'Jane Updated')
        self.assertEqual(updated_student.email, 'jane.updated@example.com')
    
    def test_student_serializer_missing_required_fields(self):
        """Test serializer validation with missing required fields."""
        invalid_data = {'name': 'John Doe'}
        
        serializer = StudentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        self.assertIn('email', serializer.errors)
        self.assertIn('dateOfBirth', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'Email address is required.')
        self.assertEqual(serializer.errors['dateOfBirth'][0], 'Date of birth is required.')
    
    def test_student_serializer_invalid_email(self):
        """Test serializer validation with invalid email."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        serializer = StudentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'Please enter a valid email address.')
    
    def test_student_serializer_future_birth_date(self):
        """Test validation for future birth date."""
        future_date = date.today() + timedelta(days=1)
        invalid_data = self.valid_data.copy()
        invalid_data['dateOfBirth'] = future_date.strftime('%Y-%m-%d')
        
        serializer = StudentSerializer(data=invalid_data, context={'request': self.request})
        with self.assertRaises(CustomAPIException) as context:
            serializer.is_valid(raise_exception=True)
        self.assertEqual(
            str(context.exception),
            "Date of birth cannot be in the future."
        )
    
    @patch('students.serializers.student_serializer.validate_unique_fields')
    def test_student_serializer_duplicate_email(self, mock_validate_unique):
        """Test validation for duplicate email."""
        mock_validate_unique.side_effect = CustomAPIException("Student with this email already exists.")
        
        duplicate_data = {
            'name': 'Another John',
            'email': self.student.email,
            'dateOfBirth': '1995-05-15'
        }
        
        serializer = StudentSerializer(data=duplicate_data)
        with self.assertRaises(CustomAPIException):
            serializer.is_valid(raise_exception=True)
    
    def test_student_read_serializer(self):
        """Test StudentReadSerializer."""
        serializer = StudentReadSerializer(self.student)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Jane Smith')
        self.assertEqual(data['email'], 'jane.smith@example.com')
        self.assertEqual(data['dateOfBirth'], '1990-01-01')
        
        for field in serializer.fields.values():
            self.assertTrue(field.read_only)


class StudentAPIViewTestCase(APITestCase):
    """Test cases for Student API views."""
    
    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.user = Account.objects.create_user(
            username='testuser',
            password='testpass',
        )
        self.client.force_authenticate(user=self.user)
        self.student_list_url = reverse('students')
        self.student_detail_url = lambda pk: reverse('student-detail', kwargs={'pk': pk})
        
        self.valid_student_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'dateOfBirth': '1995-05-15',
            'isActive': True
        }
        
        self.student = Student.objects.create(
            name='Jane Smith',
            email='jane.smith@example.com',
            date_of_birth=date(1990, 1, 1),
            created_by=self.user
        )
    
    def test_create_student_invalid_data(self):
        """Test POST request with invalid data."""
        invalid_data = {'name': 'John Doe'}  # Missing required fields
        
        response = self.client.post(
            self.student_list_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Updated assertion to match your error format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['responseCode'], '1')
        self.assertEqual(response_data['response'], 'failed')
        self.assertIn('Email address is required', response_data['error'])
    
    def test_get_student_detail_success(self):
        """Test GET request to student detail endpoint."""
        response = self.client.get(self.student_detail_url(self.student.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        # Updated to match your actual response format
        self.assertIn('data', response_data)
        student_data = response_data['data']
        self.assertEqual(student_data['name'], 'Jane Smith')
        self.assertEqual(student_data['email'], 'jane.smith@example.com')
    
    def test_get_student_detail_not_found(self):
        """Test GET request for non-existent student."""
        response = self.client.get(self.student_detail_url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_student_success(self):
        """Test PATCH request to update student."""
        update_data = {
            'name': 'Jane Updated',
            'email': 'jane.updated@example.com'
        }
        
        response = self.client.patch(
            self.student_detail_url(self.student.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.name, 'Jane Updated')
        self.assertEqual(self.student.email, 'jane.updated@example.com')
    
    def test_update_student_invalid_data(self):
        """Test PATCH request with invalid data."""
        invalid_data = {'email': 'invalid-email'}
        
        response = self.client.patch(
            self.student_detail_url(self.student.id),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # Updated assertion to match your error format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['responseCode'], '1')
        self.assertEqual(response_data['response'], 'failed')
        self.assertIn('Please enter a valid email address', response_data['error'])
    
    def test_delete_student_success(self):
        """Test DELETE request to delete student."""
        response = self.client.delete(self.student_detail_url(self.student.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        with self.assertRaises(Student.DoesNotExist):
            Student.objects.get(id=self.student.id)
    
    def test_delete_student_not_found(self):
        """Test DELETE request for non-existent student."""
        response = self.client.delete(self.student_detail_url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class StudentIntegrationTestCase(APITestCase):
    """Integration tests for complete student workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = Account.objects.create_user(
            username='testuser',
            password='testpass',
        )
        self.client.force_authenticate(user=self.user)
        self.student_list_url = reverse('students')
        self.student_detail_url = lambda pk: reverse('student-detail', kwargs={'pk': pk})
    
    def test_complete_student_lifecycle(self):
        """Test complete CRUD operations on student."""
        # Create student
        create_data = {
            'name': 'Integration Test',
            'email': 'integration@test.com',
            'dateOfBirth': '1995-01-01',
            'isActive': True
        }
        
        create_response = self.client.post(
            self.student_list_url,
            data=json.dumps(create_data),
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        
        # Read student
        student = Student.objects.get(email='integration@test.com')
        read_response = self.client.get(self.student_detail_url(student.id))
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        
        # Update student
        update_data = {'name': 'Updated Integration'}
        update_response = self.client.patch(
            self.student_detail_url(student.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # Verify update
        student.refresh_from_db()
        self.assertEqual(student.name, 'Updated Integration')
        
        # Delete student
        delete_response = self.client.delete(self.student_detail_url(student.id))
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        
        # Verify deletion
        with self.assertRaises(Student.DoesNotExist):
            Student.objects.get(id=student.id)
    
    def test_bulk_operations(self):
        """Test operations with multiple students."""
        students_data = [
            {
                'name': f'Student {i}',
                'email': f'student{i}@test.com',
                'dateOfBirth': f'199{i}-01-01',
                'isActive': True
            }
            for i in range(1, 6)
        ]
        
        for student_data in students_data:
            response = self.client.post(
                self.student_list_url,
                data=json.dumps(student_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(Student.objects.count(), 5)
        
        list_response = self.client.get(self.student_list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.json()['results']), 5)