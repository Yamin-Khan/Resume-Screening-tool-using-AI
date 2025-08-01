from django.contrib import admin
from .models import ResumeAnalysis

# Remove the duplicate registration
# admin.site.register(ResumeAnalysis)

@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ("user", "resume_file", "job_title", "industry", "ats_score", "created_at")
    list_filter = ("user", "job_title", "industry", "created_at")
    search_fields = ("user__username", "job_title", "industry")
    readonly_fields = ("created_at",)
