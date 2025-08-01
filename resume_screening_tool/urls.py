from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from screening import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('resume/', include('resume_analyzer.urls')),
    path('', views.home, name='home'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('resume/api/analyze-resume', views.analyze_resume_api, name='analyze_resume_api'),
    
    # About and Contact
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/password-change/done/'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    
    # User Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    
      
    # Pricing URL
    path('pricing/', views.pricing_view, name='pricing'),
    
    # Upgrade Plan URL
    path('upgrade-plan/', views.upgrade_plan, name='upgrade_plan'),
    
    # Features URL
    path('features/', views.features_view, name='features'),
    
    # Business URLs
    path('business/dashboard/', views.business_dashboard, name='business_dashboard'),
    path('business/profile/', views.business_profile_view, name='business_profile'),
    path('business/Edit_business_profile/', views.Edit_business_profile_view, name='Edit_business_profile'),
    path('business/signup/', views.business_signup_view, name='business_signup'),
    
    # Bulk Resume Screening URLs
    path('business/bulk-screening/', views.bulk_screening, name='bulk_screening'),
    path('business/bulk-upload-resumes/<int:bulk_id>/', views.bulk_upload_resumes, name='bulk_upload_resumes_with_id'),
    path('business/bulk-upload-resumes/', views.bulk_upload_resumes, name='bulk_upload_resumes'),
    path('business/bulk-screening-results/<int:bulk_id>/', views.bulk_screening_results, name='bulk_screening_results'),
    path('business/api/resume-result/<int:result_id>/', views.resume_result_api, name='resume_result_api'),
    path('business/export-bulk-results/<int:bulk_id>/', views.export_bulk_results, name='export_bulk_results'),
    path('business/job-portal-integration/', views.job_portal_integration, name='job_portal_integration'),
    path('business/resume/<int:resume_id>/', views.view_resume, name='view_resume'),
    
    # Chat URLs
    path('chat/', views.chat_view, name='chat'),
    path('api/chat-message/', views.chat_message_api, name='chat_message_api'),
    path('chat/clear-history/', views.clear_chat_history, name='clear_chat_history'),
    path('api/chat-history/', views.chat_history_api, name='chat_history_api'),
    
    # New API endpoint
    path('business/api/get-resume-analysis/<int:result_id>/', views.get_resume_analysis, name='get_resume_analysis'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
