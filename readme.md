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
