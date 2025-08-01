from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class Resume(models.Model):
    """Model for storing uploaded resumes."""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    resume_file = models.FileField(upload_to='resumes/')
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('failed', 'Failed')
    ], default='pending')
    predicted_role = models.CharField(max_length=200, blank=True, null=True)
    ranking = models.CharField(max_length=20, blank=True, null=True)
    confidence_score = models.FloatField(default=75.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        ordering = ['-created_at']


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    subscription_plan = models.CharField(max_length=50, choices=[
        ('free', 'Free Plan'),
        ('standard', 'Standard Plan'),
        ('premium', 'Premium Plan')
    ], default='free')
    subscription_start = models.DateTimeField(auto_now_add=True)
    subscription_end = models.DateTimeField(blank=True, null=True)
    resumes_screened = models.IntegerField(default=0)
    resumes_limit = models.IntegerField(default=25)  # Free plan limit of 25 resumes
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_subscription_active(self):
        if self.subscription_plan == 'free':
            return True
        if not self.subscription_end:
            return False
        return timezone.now() < self.subscription_end

    def can_screen_more_resumes(self):
        return self.resumes_screened < self.resumes_limit

    def get_remaining_resumes(self):
        return max(0, self.resumes_limit - self.resumes_screened)


class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50, choices=[
        ('small', '1-50 employees'),
        ('medium', '51-200 employees'),
        ('large', '201-1000 employees'),
        ('enterprise', '1000+ employees')
    ])
    company_website = models.URLField(blank=True, null=True)
    company_address = models.TextField(blank=True, null=True)
    subscription_plan = models.CharField(max_length=50, choices=[
        ('free', 'Free Plan'),
        ('standard', 'Standard Plan'),
        ('premium', 'Premium Plan'),
        ('enterprise', 'Enterprise Plan')
    ], default='free')
    subscription_start = models.DateTimeField(auto_now_add=True)
    subscription_end = models.DateTimeField(blank=True, null=True)
    resumes_screened = models.IntegerField(default=0)
    resumes_limit = models.IntegerField(default=25)  # Free plan limit of 25 resumes
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"

    def is_subscription_active(self):
        if self.subscription_plan == 'free':
            return True
        if not self.subscription_end:
            return False
        return timezone.now() < self.subscription_end

    def can_screen_more_resumes(self):
        return self.resumes_screened < self.resumes_limit

    def get_remaining_resumes(self):
        return max(0, self.resumes_limit - self.resumes_screened)


class BulkResumeScreen(models.Model):
    """Model for tracking a bulk resume screening session."""
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='bulk_screens')
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()
    required_skills = models.TextField()
    preferred_experience = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    resumes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} ({self.status}) - {self.business.company_name}"

    class Meta:
        ordering = ['-created_at']


class BulkResumeResult(models.Model):
    """Model for storing individual resume results in a bulk screening."""
    bulk_screen = models.ForeignKey(BulkResumeScreen, on_delete=models.CASCADE, related_name='results')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='bulk_results')
    match_score = models.FloatField()
    ats_score = models.FloatField()
    rank = models.IntegerField()
    strengths = models.TextField()
    weaknesses = models.TextField()
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rank {self.rank}: {self.resume.name} ({self.match_score:.1f}%)"

    class Meta:
        ordering = ['rank']


class ChatMessage(models.Model):
    """Model for storing chat messages between users and the AI assistant."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    is_user = models.BooleanField(default=True)  # True for user messages, False for AI responses
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        sender = "User" if self.is_user else "AI"
        return f"{sender}: {self.message[:50]}{'...' if len(self.message) > 50 else ''}"
    
    class Meta:
        ordering = ['created_at']



    


