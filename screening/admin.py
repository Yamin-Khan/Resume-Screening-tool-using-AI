from django.contrib import admin
from .models import Resume, ContactMessage, BusinessProfile, UserProfile, BulkResumeScreen, BulkResumeResult, ChatMessage
from django.contrib import messages
import os


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'skills')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Resume Details', {
            'fields': ('resume_file', 'skills', 'experience', 'education')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'

@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'industry', 'company_size', 'is_active')
    list_filter = ('company_size', 'is_active', 'created_at')
    search_fields = ('company_name', 'industry', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'subscription_start')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Business Information', {
            'fields': ('user', 'company_name', 'industry', 'company_size', 'company_website', 'company_address')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_end', 'resumes_screened', 'resumes_limit', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'subscription_start'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'resumes_screened', 'resumes_limit', 'is_active')
    list_filter = ('subscription_plan', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'subscription_start')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'subscription_plan', 'subscription_end', 'resumes_screened', 'resumes_limit', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'subscription_start'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_user', 'short_message', 'created_at')
    list_filter = ('is_user', 'created_at', 'user')
    search_fields = ('message', 'user__username')
    date_hierarchy = 'created_at'
    actions = ['check_ai_connectivity']
    
    def short_message(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    short_message.short_description = 'Message'
    
    def check_ai_connectivity(self, request, queryset):
        """Admin action to check OpenAI API connectivity"""
        try:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                # Use hardcoded key for testing if environment variable is not set
                api_key = "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"
                
            if api_key == 'your_openai_api_key_here':
                messages.error(request, "OpenAI API key not properly configured. The chatbot is running in offline mode.")
                return
                
            openai.api_key = api_key
            
            # Test API connectivity with a simple completion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello"}
                ],
                max_tokens=10
            )
            
            # Check if we got a valid response
            if response and response.choices and response.choices[0].message:
                messages.success(request, "AI connectivity test passed. The chatbot is online and working correctly.")
            else:
                messages.warning(request, "AI connectivity test returned an unexpected response format. The chatbot may not work correctly.")
        except Exception as e:
            messages.error(request, f"AI connectivity test failed. Error: {str(e)}")
    
    check_ai_connectivity.short_description = "Check AI API connectivity"

@admin.register(BulkResumeScreen)
class BulkResumeScreenAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'business', 'status', 'resumes_count', 'created_at')
    list_filter = ('status', 'created_at', 'business')
    search_fields = ('job_title', 'job_description', 'required_skills', 'business__company_name')
    readonly_fields = ('created_at', 'resumes_count')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Job Details', {
            'fields': ('business', 'job_title', 'job_description', 'required_skills', 'preferred_experience')
        }),
        ('Status', {
            'fields': ('status', 'resumes_count', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(BulkResumeResult)
class BulkResumeResultAdmin(admin.ModelAdmin):
    list_display = ('resume', 'bulk_screen', 'match_score', 'ats_score', 'rank')
    list_filter = ('bulk_screen', 'match_score', 'ats_score', 'rank')
    search_fields = ('resume__name', 'resume__email', 'strengths', 'weaknesses', 'bulk_screen__job_title')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Result Details', {
            'fields': ('bulk_screen', 'resume', 'match_score', 'ats_score', 'rank')
        }),
        ('Analysis', {
            'fields': ('strengths', 'weaknesses', 'recommendation')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


