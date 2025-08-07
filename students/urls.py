from django.urls import path

from students.views.reportcard_views import (
    ReportCardCreateListApiView,
    ReportCardDetailsApiView,
)
from students.views.subject_views import SubjectCreateListApiView, SubjectDetailsApiView
from .views.student_views import StudentCreateListApiView, StudentDetailsApiView

urlpatterns = [
    path("students/", StudentCreateListApiView.as_view(), name="students"),
    path("students/<pk>/", StudentDetailsApiView.as_view(), name="student-detail"),
    path("subjects/", SubjectCreateListApiView.as_view(), name="subjects"),
    path("subjects/<pk>/", SubjectDetailsApiView.as_view(), name="subject-detail"),
    # Report Card URLs
    path(
        "report-cards/",
        ReportCardCreateListApiView.as_view(),
        name="reportcard-list-create",
    ),
    path(
        "report-cards/<pk>/",
        ReportCardDetailsApiView.as_view(),
        name="reportcard-detail",
    ),
]
