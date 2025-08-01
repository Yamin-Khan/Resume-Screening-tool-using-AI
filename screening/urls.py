from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls
    path('api/chat-history/', views.chat_history_api, name='chat_history_api'),
    path('resume', views.resume_list, name='resume_list'),
    path('chat-job-recommendation/', views.chat_job_recommendation, name='chat_job_recommendation'),
    path('chat-resume-improvement/', views.chat_resume_improvement, name='chat_resume_improvement'),
    # Business API endpoints
    path('api/business/resume-result/<int:result_id>/', views.resume_result_api, name='resume_result_api'),
    path('api/business/analyze-resume/<int:result_id>/', views.get_resume_analysis, name='get_resume_analysis'),
    path('business/export-bulk-results/<int:bulk_id>/', views.export_bulk_results, name='export_bulk_results'),
    # Bulk screening URLs
    path('business/bulk-screening/', views.bulk_screening, name='bulk_screening'),
    path('business/bulk-upload-resumes/', views.bulk_upload_resumes, name='bulk_upload_resumes'),
    path('business/bulk-upload-resumes/<int:bulk_id>/', views.bulk_upload_resumes, name='bulk_upload_resumes_with_id'),
    path('business/bulk-screening-results/<int:bulk_id>/', views.bulk_screening_results, name='bulk_screening_results'),
    path('business/view-resume/<int:resume_id>/', views.view_resume, name='view_resume'),
    # ... other urls
] 