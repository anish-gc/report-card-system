# Report Card Management System


This project provides a secure Django REST API with custom token-based authentication, student , reportcard.

## 🌟 Features

- Custom token authentication with AES encryption
- Session management with expiry
- Student, Subject, Mark, and Report Card management
- Bulk operations for marks and calculations
- Performance analytics endpoints


## 🔧 Technology Stack

- **Backend**: Django 5.2+
- **Database**: PostgreSQL 16+
- **API**: Django REST Framework

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- Python 3.12+ 
- PostgreSQL 16+
- Git
- pip
- virtualenv (optional for development)

## 🚀 Getting Started

Follow these steps to set up and run the project locally:

### 1. Clone the Repository

```bash
git clone git@github.com:anish-gc/report-card-system.git
cd report-card-system
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements/development.txt
```

### 4. Configure PostgreSQL

Make sure PostgreSQL is installed and running. Create a database for the project:

```bash
# Access PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE report_card_system;

# Exit PostgreSQL
\q
```

### 5. Environment Variables

Create a `.env` file in the project root (You can take sample from .env-sample. Just copy all the contents to .env):

```
DEBUG=True
MODE=development
SECRET_KEY=your_secret_key_here
DB_NAME=urdb
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Superuser

```bash
python manage.py createsuperuser
```


### 8. Run the development Server

```bash
python manage.py runserver
```

The application should now be accessible at http://localhost:8000.

## 🗂️ Project Structure

```
edurag-intelligent-teacher-using-rag-and-langchain/
├── accounts
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── management
│   ├── migrations
│   ├── models.py
│   ├── __pycache__
│   ├── tests.py
│   └── views.py
├── authentication
│   ├── __pycache__
│   ├── urls.py
│   ├── validation.py
│   └── views.py
├── core
│   ├── asgi.py
│   ├── celery.py
│   ├── __init__.py
│   ├── __pycache__
│   ├── settings
│   ├── urls.py
│   └── wsgi.py
├── debug.log
├── manage.py
├── readme.md
├── requirements
│   └── development.txt
├── students
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── managers
│   ├── migrations
│   ├── models
│   ├── __pycache__
│   ├── serializers
│   ├── signals.py
│   ├── tasks.py
│   ├── tests
│   ├── urls.py
│   └── views
├── utilities
│   ├── base_model.py
│   ├── base_serializer.py
│   ├── custom_authentication_class.py
│   ├── custom_encryption_class.py
│   ├── custom_exception_class.py
│   ├── custom_global_filter.py
│   ├── custom_pagination_class.py
│   ├── custom_permission_class.py
│   ├── custom_response_class.py
│   ├── global_functions.py
│   ├── global_parameters.py
│   ├── __pycache__
│   ├── serializer_utils.py
│   └── views.py


```

## Authentication

### Login

**Endpoint:**  
`POST /api/login/`

**Request:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "You are logged in successfully",
    "data": {
        "token": "OWNDEU5+P6iN6IYWJi/B14e0IPTgfl1Yix5m8g/bRX30QDY1hoptX/5Agc04/wiXrTMBV4eoO4qUHW2NtDwVWA==",
        "designation": "superadmin",
        "username": "anishchengre",
        "sessionTime": 200,
        "sessionRenewed": false
    }
}
```

**Error Responses:**

- Invalid credentials (401 Unauthorized):
```json
{"responseCode":"1","response":"customResponse","message":"We couldnot find the account with given username"}
```



**Usage Notes:**
1. The returned `token` must be included in subsequent requests in the Authorization header:
   ```
   Authorization: Token OWNDEU5+P6iN6IYWJi/B14e0IPTgfl1Yix5m8g/bRX30QDY1hoptX/5Agc04/wiXrTMBV4eoO4qUHW2NtDwVWA==
   ```
2. `sessionTime` is in minutes until expiration
3. `sessionRenewed` indicates if an existing session was extended


```
## Student Management

### List Students
**Endpoint:**  
`GET /api/students/`

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 10)
- `search` - Search by name or email
- `is_active` - Filter by active status (true/false)

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Success",
    "results": [
        {
            "referenceId": "1",
            "isActive": true,
            "createdAt": "2025-08-08T20:59:18.555912+05:45",
            "name": "Manish Khanal",
            "email": "manishkhanal@gmail.com",
            "dateOfBirth": "2001-03-15"
        }
    ],
    "count": 1,
    "pageSize": 10,
    "currentPage": 1,
    "totalPages": 1,
    "links": {
        "next": null,
        "previous": null,
        "first": "http://localhost:8000/students/?page=1",
        "last": "http://localhost:8000/students/?page=1"
    }
}
```

### Create Student
**Endpoint:**  
`POST /students/`

**Request Body:**
```json
{
    "name": "New Student",
    "email": "new.student@example.com",
    "dateOfBirth": "2002-05-20",
    "isActive": true
}
```

**Success Response (201 Created):**
```json
{
    "responseCode": "0",
    "message": "Student created successfully."
}
```

**Error Responses:**
- Duplicate email (400 Bad Request):
```json
{
    "responseCode": "1",
    "response": "customResponse",
    "error": "Student with Email 'manishkhanal@gmail.com' already exists."
}
```

- Missing required field (400 Bad Request):
```json
{
    "responseCode": "1",
    "error": "Email field is required"
}
```

### Student Detail Operations
**Endpoint:**  
`GET/PUT/DELETE /students/<id>/`

**Successful Responses:**
- Get Student (200 OK):
```json
{
    "responseCode": "0",
    "message": "Success",
    "data": {
        "referenceId": "1",
        "isActive": true,
        "createdAt": "2025-08-08T20:59:18.555912+05:45",
        "name": "Manish Khanal",
        "email": "manishkhanal@gmail.com",
        "dateOfBirth": "2001-03-15"
    }
}
```

- Update Student (200 OK):
```json
{
    "responseCode": "0",
    "message": "Student updated successfully."
}
```


**Usage Notes:**
1. All operations require authentication token
2. `referenceId` is the unique identifier for each student
3. Dates should be in ISO 8601 format (YYYY-MM-DD)
4. For PUT operations, include all required fields


## Subject Management

### List Subjects
**Endpoint:**  
`GET /subjects/`

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 10)

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Success",
    "results": [
        {
            "referenceId": "3",
            "isActive": true,
            "createdAt": "2025-08-08T21:00:00.140704+05:45",
            "name": "English",
            "code": "ENG101"
        },
        {
            "referenceId": "2",
            "isActive": true,
            "createdAt": "2025-08-08T20:59:46.366298+05:45",
            "name": "Maths",
            "code": "MTH101"
        },
        
    ],
    "count": 3,
    "pageSize": 10,
    "currentPage": 1,
    "totalPages": 1,
    "links": {
        "next": null,
        "previous": null,
        "first": "http://localhost:8000/subjects/?page=1",
        "last": "http://localhost:8000/subjects/?page=1"
    }
}
```

### Create Subject
**Endpoint:**  
`POST /subjects/`

**Request Body:**
```json
{
    "name": "New Subject",
    "code": "NEW101",
}
```

**Success Response (201 Created):**
```json
{
    "responseCode": "0",
    "message": "Subject created successfully."
}
```

**Error Responses:**
- Duplicate subject code (400 Bad Request):
```json
{
    "responseCode": "1",
    "response": "customResponse",
    "error": "Subject with Code 'SCI101' already exists."
}
```

- Invalid code format (400 Bad Request):
```json
{
    "responseCode": "1",
    "response": "customResponse",
    "error": "Subject code must be 2-4 uppercase letters followed by 2-4 numbers (e.g., MATH101)."
}
```

- Missing required field (400 Bad Request):
```json
{
    "responseCode": "2",
    "error": "Name field is required"
}
```

### Subject Detail Operations
**Endpoint:**  
`GET/PUT/DELETE /subjects/<id>/`

**Successful Responses:**
- Get Subject (200 OK):
```json
{
    "responseCode": "0",
    "message": "Success",
    "data": {
        "referenceId": "1",
        "isActive": true,
        "createdAt": "2025-08-08T20:59:38.162525+05:45",
        "name": "Science",
        "code": "SCI101"
    }
}
```

- Update Subject (200 OK):
```json
{
    "responseCode": "0",
    "message": "Subject updated successfully."
}
```



- Trying to update to existing code (400 Bad Request):
```json
{
    "responseCode": "1",
    "error": "Subject code 'MTH101' is already in use"
}
```

**Usage Notes:**
1. Subject `code` must follow the format:
   - 2-4 uppercase letters
   - Followed by 2-4 numbers
   - Example valid codes: `CS101`, `MATH202`, `PHY404`
2. All operations require authentication token
3. `referenceId` is the unique identifier for each subject
4. When updating, you cannot modify the `code` to match an existing subject


## Report Card Management

### Create Report Card
**Endpoint:**  
`POST /report-cards/`

**Request Body:**
```json
{
    "student": "2",
    "term": "Term 1",
    "year": "2025",
    "marks": [
        {
            "subject": "1",
            "score": "80"
        },
        {
            "subject": "2",
            "score": "80"
        },
        {
            "subject": "3",
            "score": "99"
        }
    ]
}
```

**Success Response (201 Created):**
```json
{
    "responseCode": "0",
    "message": "Report card created successfully. Calculations are being processed in the background.",
    "data": {
        "reportCardreferenceId": "2",
        "studentReferenceId": "2",
        "studentName": "Mandip Khanal",
        "term": "Term 1",
        "year": 2025,
        "totalSubjects": 3,
        "averageScore": "86.33",
        "totalScore": "259.00",
        "highestScore": "99.00",
        "lowestScore": "80.00",
        "grade": null,
        "percentage": "0.00",
        "calculationStatus": "calculating",
        "lastCalculated": null,
        "marks": [
            {
                "marksReferenceId": "72",
                "subjectreferenceId": "3",
                "subjectName": "English",
                "subjectCode": "ENG101",
                "score": "99.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "71",
                "subjectreferenceId": "2",
                "subjectName": "Maths",
                "subjectCode": "MTH101",
                "score": "80.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "70",
                "subjectreferenceId": "1",
                "subjectName": "Science",
                "subjectCode": "SCI101",
                "score": "80.00",
                "remarks": ""
            }
        ],
        "calculationTaskId": "576a9740-6cd2-4346-b39c-e0c82fc4a646"
    }
}
```

**Error Responses:**
- Invalid term (400 Bad Request):
```json
{
    "responseCode": "1",
    "response": "failed",
    "error": "Invalid term choice. Please choose Term 1, Term 2, Term 3 or Final"
}
```

- Duplicate report card (400 Bad Request):
```json
{
    "responseCode": "1",
    "error": "Report card already exists for this student, term and year combination"
}
```

### List Report Cards
**Endpoint:**  
`GET /api/report-cards/`

**Query Parameters:**
- `year` - Filter by academic year (e.g., 2025)
- `term` - Filter by term ("Term 1", "Term 2", "Term 3", "Final")
- `student_id` - Filter by student reference ID
- `detailed` - Include full mark details (true/false, default: false)
- `include_class_stats` - Include class statistics (true/false, default: false)

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Report cards retrieved successfully.",
    "data": {
        "report_cards": [
            {
                "reportCardreferenceId": "2",
                "studentReferenceId": "2",
                "studentName": "Mandip Khanal",
                "term": "Term 1",
                "year": 2025,
                "totalSubjects": 3,
                "averageScore": "86.33",
                "totalScore": "259.00",
                "highestScore": "99.00",
                "lowestScore": "80.00",
                "grade": null,
                "percentage": "0.00",
                "calculationStatus": "calculating",
                "lastCalculated": null,
                "marks": [
                    {
                        "marksReferenceId": "72",
                        "subjectreferenceId": "3",
                        "subjectName": "English",
                        "subjectCode": "ENG101",
                        "score": "99.00",
                        "remarks": ""
                    },
                    {
                        "marksReferenceId": "71",
                        "subjectreferenceId": "2",
                        "subjectName": "Maths",
                        "subjectCode": "MTH101",
                        "score": "80.00",
                        "remarks": ""
                    },
                    {
                        "marksReferenceId": "70",
                        "subjectreferenceId": "1",
                        "subjectName": "Science",
                        "subjectCode": "SCI101",
                        "score": "80.00",
                        "remarks": ""
                    }
                ]
            }
        ]
    }
}
```

### Retrieve Report Card
**Endpoint:**  
`GET /report-cards/<id>/`

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Report card retrieved successfully.",
    "data": {
        "reportCardreferenceId": "1",
        "studentReferenceId": "1",
        "studentName": "Manish Khanal Updated",
        "term": "Term 1",
        "year": 2025,
        "totalSubjects": 3,
        "averageScore": "90.00",
        "totalScore": "270.00",
        "highestScore": "90.00",
        "lowestScore": "90.00",
        "grade": "A",
        "percentage": "90.00",
        "calculationStatus": "completed",
        "lastCalculated": "2025-08-08T22:35:40.378368+05:45",
        "marks": [
            {
                "marksReferenceId": "69",
                "subjectreferenceId": "3",
                "subjectName": "English",
                "subjectCode": "ENG101",
                "score": "90.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "68",
                "subjectreferenceId": "2",
                "subjectName": "Maths",
                "subjectCode": "MTH101",
                "score": "90.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "67",
                "subjectreferenceId": "1",
                "subjectName": "Science",
                "subjectCode": "SCI101",
                "score": "90.00",
                "remarks": ""
            }
        ]
    }
}
```

### Update Report Card
**Endpoint:**  
`PUT /report-cards/<id>/`

**Request Body:**
```json
{
    "term": "Term 1",
    "year": "2025",
    "marks": [
        {
            "subject": "1",
            "score": "90"
        },
        {
            "subject": "2",
            "score": "90"
        },
        {
            "subject": "3",
            "score": "90"
        }
    ]
}
```

**Success Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Report card updated successfully. Calculations are being processed in the background.",
    "data": {
        "reportCardreferenceId": "1",
        "studentReferenceId": "1",
        "studentName": "Manish Khanal Updated",
        "term": "Term 1",
        "year": 2025,
        "totalSubjects": 3,
        "averageScore": "90.00",
        "totalScore": "270.00",
        "highestScore": "90.00",
        "lowestScore": "90.00",
        "grade": "A",
        "percentage": "90.00",
        "calculationStatus": "calculating",
        "lastCalculated": "2025-08-08T22:35:40.378368+05:45",
        "marks": [
            {
                "marksReferenceId": "75",
                "subjectreferenceId": "3",
                "subjectName": "English",
                "subjectCode": "ENG101",
                "score": "90.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "74",
                "subjectreferenceId": "2",
                "subjectName": "Maths",
                "subjectCode": "MTH101",
                "score": "90.00",
                "remarks": ""
            },
            {
                "marksReferenceId": "73",
                "subjectreferenceId": "1",
                "subjectName": "Science",
                "subjectCode": "SCI101",
                "score": "90.00",
                "remarks": ""
            }
        ],
        "calculationTaskId": "18dddd6f-daae-4101-9b5c-0cbaf72cc4a7"
    }
}
```

**Usage Notes:**
1. Valid term values: "Term 1", "Term 2", "Term 3", "Final"
2. Calculations are processed asynchronously - check status using the task ID
3. When updating, all marks must be included (full replacement, not partial update)
4. The `calculationStatus` can be: "pending", "calculating", "completed", or "failed"
5. For large datasets, use `detailed=false` when listing to improve performance
6. Class statistics (when requested) include: class average, highest/lowest scores, grade distribution



## Student Performance Analysis

### Get Student Performance
**Endpoint:**  
`GET /students/<student_id>/performance/`

**Description:**  
Retrieves comprehensive performance data for a specific student including all report cards and subject-wise averages for a given year.

**Required Query Parameter:**
- `year` - Academic year to analyze (e.g., 2025)

**Successful Response (200 OK):**
```json
{
    "responseCode": "0",
    "message": "Student performance retrieved successfully. Some calculations are being updated in the background.",
    "data": {
        "reportCards": [
            {
                "reportCardreferenceId": "1",
                "studentReferenceId": "1",
                "studentName": "Manish Khanal Updated",
                "term": "Term 1",
                "year": 2025,
                "totalSubjects": 3,
                "averageScore": "90.00",
                "totalScore": "270.00",
                "highestScore": "90.00",
                "lowestScore": "90.00",
                "grade": "A",
                "percentage": "90.00",
                "calculationStatus": "calculating",
                "lastCalculated": "2025-08-08T22:35:40.378368+05:45",
                "marks": [
                    {
                        "marksReferenceId": "75",
                        "subjectreferenceId": "3",
                        "subjectName": "English",
                        "subjectCode": "ENG101",
                        "score": "90.00",
                        "remarks": ""
                    },
                    {
                        "marksReferenceId": "74",
                        "subjectreferenceId": "2",
                        "subjectName": "Maths",
                        "subjectCode": "MTH101",
                        "score": "90.00",
                        "remarks": ""
                    },
                    {
                        "marksReferenceId": "73",
                        "subjectreferenceId": "1",
                        "subjectName": "Science",
                        "subjectCode": "SCI101",
                        "score": "90.00",
                        "remarks": ""
                    }
                ]
            }
        ],
        "performanceSummary": {
            "studentReferenceId": "1",
            "year": 2025,
            "subjectAverages": [
                {
                    "subjectCode": "ENG101",
                    "subjectName": "English",
                    "averageScore": 90.0,
                    "termCount": 1
                },
                {
                    "subjectCode": "MTH101",
                    "subjectName": "Maths",
                    "averageScore": 90.0,
                    "termCount": 1
                },
                {
                    "subjectCode": "SCI101",
                    "subjectName": "Science",
                    "averageScore": 90.0,
                    "termCount": 1
                }
            ],
            "overallAverage": "90.0000000000000000"
        },
        "backgroundTasks": {
            "performance_calculation_task_id": "0a0a9e1a-880f-4dbb-8879-d8eb80cb7c47",
            "report_cards_being_calculated": [
                {
                    "reporCardId": "1",
                    "taskId": "d5cc5593-c1be-4f3e-9852-efd595c0c9dd"
                }
            ]
        }
    }
}
```

**Error Responses:**
- Missing year parameter (400 Bad Request):
```json
{
    "responseCode": "1",
    "error": "Year parameter is required"
}
```

- Invalid student ID (404 Not Found):
```json
{
    "responseCode": "3",
    "error": "Student not found"
}
```

- No data for specified year (404 Not Found):
```json
{
    "responseCode": "4",
    "error": "No performance data available for the specified year"
}
```

**Usage Notes:**
1. The endpoint provides three main data sections:
   - `reportCards`: All report cards for the student in the specified year
   - `performanceSummary`: Aggregated performance metrics including:
     - Subject-wise averages
     - Overall average score
     - Term participation count
   - `backgroundTasks`: Information about ongoing calculations

2. Performance calculations may be processed asynchronously:
   - Check status using the provided task IDs
   - `calculationStatus` values: "pending", "calculating", "completed", "failed"

3. The response includes detailed mark breakdowns for each report card

4. Example cURL request:
```bash
curl -X GET "http://localhost:8000/api/students/1/performance/?year=2025" \
  -H "Authorization: Token your_token_here"
```

5. For large datasets, the response may be paginated (check for `next` and `previous` links in the response)