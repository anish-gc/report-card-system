from django.urls import path

from students.views.mark_views import (
    BulkMarkCreateApiView,
    MarkCreateListApiView,
    MarkDetailsApiView,
    SubjectPerformanceApiView,
)
from students.views.reportcard_views import (
    ReportCardCreateListApiView,
    ReportCardDetailsApiView,
    StudentPerformanceApiView,
)
from students.views.subject_views import SubjectCreateListApiView, SubjectDetailsApiView
from .views.student_views import StudentCreateListApiView, StudentDetailsApiView

urlpatterns = [
    path("students/", StudentCreateListApiView.as_view(), name="students"),
    path("students/<pk>/", StudentDetailsApiView.as_view(), name="student-detail"),

    path("subjects/", SubjectCreateListApiView.as_view(), name="subjects"),
    path("subjects/<pk>/", SubjectDetailsApiView.as_view(), name="subject-detail"),

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

    path("marks/", MarkCreateListApiView.as_view(), name="mark-list-create"),
    path("marks/<pk>/", MarkDetailsApiView.as_view(), name="mark-detail"),
    path(
        "marks/bulk-create/", BulkMarkCreateApiView.as_view(), name="mark-bulk-create"
    ),
    
    path(
        "students/<pk>/performance/",
        StudentPerformanceApiView.as_view(),
        name="student-performance",
    ),
    path(
        "subjects/<int:subject_id>/performance/",
        SubjectPerformanceApiView.as_view(),
        name="subject-performance",
    ),
]
