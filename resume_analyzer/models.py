from django.db import models
from django.contrib.auth.models import User
import json
from django.utils import timezone

class ResumeAnalysis(models.Model):
    """Model to store resume analysis results for authenticated users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resume_analyses')
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    file_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    ats_score = models.IntegerField(default=0)
    analysis_data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Resume Analyses'
    
    def __str__(self):
        return f"{self.user.username}'s resume analysis - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_content_score(self):
        """Get content score from the analysis data."""
        try:
            return self.analysis_data['content_score']
        except (KeyError, TypeError):
            return 0
    
    def get_keywords_score(self):
        """Get keywords score from the analysis data."""
        try:
            return self.analysis_data['keywords_score']
        except (KeyError, TypeError):
            return 0
    
    def get_strengths(self):
        """Get strengths from the analysis data."""
        try:
            return self.analysis_data['strengths']
        except (KeyError, TypeError):
            return []
    
    def get_improvements(self):
        """Get improvements from the analysis data."""
        try:
            return self.analysis_data['improvements']
        except (KeyError, TypeError):
            return []
    
    def get_keywords(self):
        """Get keywords from the analysis data."""
        try:
            return self.analysis_data['keywords']
        except (KeyError, TypeError):
            return []
    
    def get_experience(self):
        """Get experience from the analysis data."""
        try:
            return self.analysis_data['experience']
        except (KeyError, TypeError):
            return []
            
    def get_technical_skills(self):
        """Get technical skills from the analysis data."""
        try:
            return self.analysis_data.get('technical_skills', [])
        except (KeyError, TypeError):
            return []
            
    def get_soft_skills(self):
        """Get soft skills from the analysis data."""
        try:
            return self.analysis_data.get('soft_skills', [])
        except (KeyError, TypeError):
            return []
            
    def get_missing_skills(self):
        """Get missing skills from the analysis data."""
        try:
            return self.analysis_data.get('missing_skills', [])
        except (KeyError, TypeError):
            return []
            
    def get_improvement_areas(self):
        """Get improvement areas from the analysis data."""
        try:
            # Check for 'improvement_areas' first, then fall back to 'improvements'
            return self.analysis_data.get('improvement_areas', self.analysis_data.get('improvements', []))
        except (KeyError, TypeError):
            return []
