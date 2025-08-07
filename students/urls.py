from django.urls import path

from students.views.subject_views import SubjectCreateListApiView, SubjectDetailsApiView
from .views.student_views import StudentCreateListApiView, StudentDetailsApiView

urlpatterns = [
    path('students/', StudentCreateListApiView.as_view(), name='students'),
    path('students/<pk>/', StudentDetailsApiView.as_view(), name='student-detail'),
     path('subjects/', SubjectCreateListApiView.as_view(), name='subjects'),
    path('subjects/<pk>/', SubjectDetailsApiView.as_view(), name='subject-detail')
]