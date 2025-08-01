from django.urls import path
from . import views

urlpatterns = [
    path('api/analyze-resume', views.analyze_resume, name='analyze_resume'),
    path('my-resumes/', views.user_resume_list, name='user_resume_list'),
    path('resume-detail/<int:analysis_id>/', views.resume_detail, name='resume_detail'),
] 