from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .models import Resume, ContactMessage, BusinessProfile, UserProfile, BulkResumeScreen, BulkResumeResult, ChatMessage
from .forms import ContactForm, ProfileUpdateForm, ChatMessageForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from decimal import Decimal
from django.db.models import Avg
from resume_analyzer.models import ResumeAnalysis
from collections import Counter
from django.utils import timezone
from django.http import JsonResponse
from .forms import BusinessSignupForm, BusinessProfileUpdateForm, UserTypeForm
import random
import csv
from django.http import HttpResponse
import json
from resume_analyzer.views import analyze_resume
from django.views.decorators.http import require_POST
import os
import re
from .utils import analyze_resume_for_job, analyze_resume_for_job_direct
import logging
import traceback
import requests
from .utils import extract_text_from_resume

# Define logger
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

def upload_resume(request):
    # Check if user is authenticated and is a business user
    if request.user.is_authenticated:
        try:
            business_profile = request.user.business_profile
            # Redirect to bulk screening for business users
            return redirect('bulk_screening')
        except BusinessProfile.DoesNotExist:
            # Continue with regular resume upload
            # Get or create user profile
            try:
                user_profile = request.user.user_profile
            except UserProfile.DoesNotExist:
                user_profile = UserProfile.objects.create(
                    user=request.user,
                    subscription_plan='free',
                    resumes_limit=25
                )
                
            # Check if user can upload more resumes
            if not user_profile.can_screen_more_resumes():
                messages.warning(request, f'You have reached your limit of {user_profile.resumes_limit} resumes. Please upgrade your plan to continue.')
                return redirect('pricing')
    
    # Initialize context with empty results
    context = {
        'show_results': False
    }
    
    if request.method == 'POST' and request.user.is_authenticated:
        # Handle file upload logic here
        
        # Update resume count for the user
        try:
            user_profile = request.user.user_profile
            user_profile.resumes_screened += 1
            user_profile.save()
        except Exception as e:
            # Log the error but don't block the user
            print(f"Error updating resume count: {str(e)}")
            
        messages.success(request, 'Resume uploaded successfully!')
        return redirect('dashboard')
        
    return render(request, 'upload_resume.html', context)

@login_required
def dashboard(request):
    # Check if the user is a business user
    try:
        business_profile = request.user.business_profile
        # Redirect to business dashboard
        return redirect('business_dashboard')
    except BusinessProfile.DoesNotExist:
        # Continue with regular user dashboard
        pass
    
    # Get or create user profile
    try:
        user_profile = request.user.user_profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(
            user=request.user,
            subscription_plan='free',
            resumes_limit=25
        )
    
    # Get all resume analyses for the current user
    analyses = ResumeAnalysis.objects.filter(user=request.user).order_by('-created_at')
    resume_count = analyses.count()
    
    # Check subscription status
    remaining_resumes = user_profile.get_remaining_resumes()
    subscription_active = user_profile.is_subscription_active()
    subscription_plan = user_profile.subscription_plan.capitalize()
    
    # Calculate statistics
    high_score_count = analyses.filter(ats_score__gte=80).count()
    medium_score_count = analyses.filter(ats_score__gte=60, ats_score__lt=80).count()
    average_score_count = analyses.filter(ats_score__gte=40, ats_score__lt=60).count()
    low_score_count = analyses.filter(ats_score__lt=40).count()
    
    # Calculate average ATS score
    avg_score = 0
    if resume_count > 0:
        avg_score = int(analyses.aggregate(Avg('ats_score'))['ats_score__avg'])
    
    # Get recent analyses (limit to 5)
    recent_analyses = analyses[:5]
    
    # Get timeline data (last 10 analyses in chronological order)
    recent_timeline = list(analyses.order_by('created_at'))[-10:]
    
    # Extract top skills, common issues, and recommended skills
    top_skills = []
    common_issues = []
    recommended_skills = []
    
    if resume_count > 0:
        # Collect all skills and issues
        all_technical_skills = []
        all_soft_skills = []
        all_missing_skills = []
        all_improvement_areas = []
        
        for analysis in analyses:
            # Extract skills
            all_technical_skills.extend(analysis.get_technical_skills())
            all_soft_skills.extend(analysis.get_soft_skills())
            all_missing_skills.extend(analysis.get_missing_skills())
            all_improvement_areas.extend(analysis.get_improvement_areas())
        
        # Get most frequent technical and soft skills (top 5)
        if all_technical_skills or all_soft_skills:
            skill_counter = Counter(all_technical_skills + all_soft_skills)
            top_skills = [skill for skill, _ in skill_counter.most_common(5)]
        
        # Get most common improvement areas (top 3)
        if all_improvement_areas:
            issue_counter = Counter(all_improvement_areas)
            common_issues = [issue for issue, _ in issue_counter.most_common(3)]
        
        # Get most frequent missing skills (top 5)
        if all_missing_skills:
            missing_skill_counter = Counter(all_missing_skills)
            recommended_skills = [skill for skill, _ in missing_skill_counter.most_common(5)]
    
    context = {
        'resume_count': resume_count,
        'high_score_count': high_score_count,
        'medium_score_count': medium_score_count,
        'average_score_count': average_score_count,
        'low_score_count': low_score_count,
        'avg_score': avg_score,
        'recent_analyses': recent_analyses,
        'recent_timeline': recent_timeline,
        'top_skills': top_skills,
        'common_issues': common_issues,
        'recommended_skills': recommended_skills,
        'user_profile': user_profile,
        'subscription_plan': subscription_plan,
        'subscription_active': subscription_active,
        'remaining_resumes': remaining_resumes,
        'resumes_limit': user_profile.resumes_limit,
        'resumes_screened': user_profile.resumes_screened,
    }
    return render(request, 'User_dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            
            # Check if this is a business user
            try:
                business_profile = user.business_profile
                # Redirect to business dashboard
                return redirect('business_dashboard')
            except BusinessProfile.DoesNotExist:
                # Regular user - redirect to home
                return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')

def signup(request):
    if request.method == 'POST':
        # First check if the user wants to register as an individual or business
        user_type = request.POST.get('user_type', 'individual')
        
        # Initialize the forms here so they're available in all code paths
        user_type_form = UserTypeForm(request.POST)
        business_form = BusinessSignupForm()  # Initialize empty business form
        
        if user_type == 'business':
            business_form = BusinessSignupForm(request.POST)
            if business_form.is_valid():
                user = business_form.save()
                
                # Create business profile
                BusinessProfile.objects.create(
                    user=user,
                    company_name=business_form.cleaned_data['company_name'],
                    industry=business_form.cleaned_data['industry'],
                    company_size=business_form.cleaned_data['company_size'],
                    company_website=business_form.cleaned_data['company_website'],
                    company_address=business_form.cleaned_data['company_address'],
                )
                
                login(request, user)
                messages.success(request, 'Business account created successfully!')
                return redirect('business_dashboard')
            else:
                # Add explicit error messaging for debugging
                for field, errors in business_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        else:
            # Regular user signup
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match!')
                return render(request, 'registration/signup.html', {'user_type_form': user_type_form, 'business_form': business_form})
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
                return render(request, 'registration/signup.html', {'user_type_form': user_type_form, 'business_form': business_form})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists!')
                return render(request, 'registration/signup.html', {'user_type_form': user_type_form, 'business_form': business_form})
            
            # Create the user
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                # Create a user profile with free plan
                UserProfile.objects.create(
                    user=user,
                    subscription_plan='free',
                    resumes_limit=25  # Free tier allows 25 resumes
                )
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('upload_resume')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    else:
        # Show user type selection form first
        user_type_form = UserTypeForm()
        business_form = BusinessSignupForm()
    
    context = {
        'user_type_form': user_type_form,
        'business_form': business_form
    }
    return render(request, 'registration/signup.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('/')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Add password reset logic here
            messages.success(request, 'Password reset instructions sent to your email.')
            logout(request)
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
    return render(request, 'registration/password_reset_form.html')
    

@login_required
def profile_view(request):
    # Check if user is a business user
    try:
        business_profile = request.user.business_profile
        # Redirect to business profile
        return redirect('business_profile')
    except BusinessProfile.DoesNotExist:
        # Continue with regular user profile
        pass
        
    # Get the count of resume analyses for this user
    resume_count = ResumeAnalysis.objects.filter(user=request.user).count()
    
    # Get recent resume analyses (limit to 5)
    recent_analyses = ResumeAnalysis.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'resume_count': resume_count,
        'recent_analyses': recent_analyses,
    }
    return render(request, 'profile.html', context)

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # If password was changed, update the session
            if form.cleaned_data.get('new_password1'):
                user = authenticate(username=request.user.username, 
                                   password=form.cleaned_data.get('new_password1'))
                if user:
                    login(request, user)
                    messages.success(request, 'Your profile and password have been updated successfully!')
                else:
                    messages.success(request, 'Your profile has been updated, but there was an issue with the new login session. Please log in again.')
                    return redirect('login')
            else:
                messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'profile_update.html', context)



# About and Contact pages
def about_view(request):
    return render(request, 'about_features.html')

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL 

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            User.objects.get(email=email)
            return super().form_valid(form)
        except User.DoesNotExist:
            messages.error(self.request, 'No user found with this email address.')
            return self.form_invalid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # If user is authenticated, use their info
            if request.user.is_authenticated:
                contact_message = form.save(commit=False)
                contact_message.name = request.user.first_name or request.user.username or request.user.last_name
                contact_message.email = request.user.email
                contact_message.save()
            else:
                form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form
    }
    return render(request, "contact.html", context)

def pricing_view(request):
    context = {}
    
    if request.user.is_authenticated:
        # Check if user is a business user
        try:
            business_profile = request.user.business_profile
            context['business_profile'] = business_profile
        except BusinessProfile.DoesNotExist:
            # Check regular user profile
            try:
                user_profile = request.user.user_profile
                context['user_profile'] = user_profile
            except UserProfile.DoesNotExist:
                # Create user profile if it doesn't exist
                user_profile = UserProfile.objects.create(
                    user=request.user,
                    subscription_plan='free',
                    resumes_limit=25
                )
                context['user_profile'] = user_profile
    
    return render(request, 'pricing.html', context)

@login_required
def upgrade_plan(request):
    plan = request.GET.get('plan', 'standard')
    
    # Set plan limits based on the selected plan
    if plan == 'free':
        plan_name = 'Free'
        resume_limit = 25
        price = '$0/month'
    elif plan == 'standard':
        plan_name = 'Standard'
        resume_limit = 100
        price = '$19/month'
    elif plan == 'premium':
        plan_name = 'Premium'
        resume_limit = 1000
        price = '$49/month'
    else:
        # Default to standard if somehow an invalid plan is passed
        plan_name = 'Standard'
        resume_limit = 100
        price = '$19/month'
    
    # Check if user is a business user
    is_business = False
    
    try:
        business_profile = request.user.business_profile
        is_business = True
        context = {
            'business_profile': business_profile,
        }
    except BusinessProfile.DoesNotExist:
        # Try to get or create user profile
        try:
            user_profile = request.user.user_profile
        except UserProfile.DoesNotExist:
            user_profile = UserProfile.objects.create(
                user=request.user,
                subscription_plan='free',
                resumes_limit=25
            )
        context = {
            'user_profile': user_profile,
        }
    
    # Add plan information to context
    context.update({
        'plan': plan_name,
        'resume_limit': resume_limit,
        'price': price,
        'is_business': is_business,
    })
    
    # Process the payment form if submitted
    if request.method == 'POST':
        success = False
        
        try:
            # This would be where you handle the payment processing
            # For now, we'll just update the user's subscription
            
            if is_business:
                # Update business profile
                business_profile.subscription_plan = plan.lower()
                business_profile.resumes_limit = resume_limit
                business_profile.subscription_start = timezone.now()
                
                # Set subscription end date to 30 days from now for paid plans
                if plan.lower() != 'free':
                    business_profile.subscription_end = timezone.now() + timezone.timedelta(days=30)
                
                business_profile.save()
                success = True
            else:
                # Update the user profile with subscription details
                user_profile.subscription_plan = plan.lower()
                user_profile.resumes_limit = resume_limit
                user_profile.subscription_start = timezone.now()
                
                # Set subscription end date to 30 days from now for paid plans
                if plan.lower() != 'free':
                    user_profile.subscription_end = timezone.now() + timezone.timedelta(days=30)
                
                user_profile.save()
                success = True
            
            if success:
                messages.success(request, f'Your subscription has been updated to the {plan_name} plan!')
                
                # Redirect to pricing page to show the updated subscription
                return redirect('pricing')
                
        except Exception as e:
            messages.error(request, f'There was an error updating your subscription: {str(e)}')
    
    return render(request, 'upgrade_plan.html', context)

def features_view(request):
    return redirect('about')

@login_required
def business_dashboard(request):
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    # Check subscription status
    remaining_resumes = business_profile.get_remaining_resumes()
    subscription_active = business_profile.is_subscription_active()
    subscription_plan = business_profile.subscription_plan.capitalize()
    
    # Get recent bulk screening sessions
    recent_screenings = BulkResumeScreen.objects.filter(business=business_profile).order_by('-created_at')[:5]
    
    # Get recent screening results
    recent_results = BulkResumeResult.objects.filter(
        bulk_screen__business=business_profile
    ).order_by('-created_at')[:5]
    
    # Calculate statistics
    total_resumes = Resume.objects.filter(bulk_results__bulk_screen__business=business_profile).distinct().count()
    total_screenings = BulkResumeScreen.objects.filter(business=business_profile).count()
    total_bulk_screenings = BulkResumeScreen.objects.filter(business=business_profile).count()
    
    # Calculate growth percentages (placeholder values for now)
    resume_growth = 10  # Placeholder
    screening_growth = 15  # Placeholder
    bulk_screening_growth = 20  # Placeholder
    
    # Prepare stats dictionary
    stats = {
        'total_resumes': total_resumes,
        'total_screenings': total_screenings,
        'total_bulk_screenings': total_bulk_screenings,
        'total_jobs': total_screenings,  # Using screenings as jobs for now
        'resume_growth': resume_growth,
        'screening_growth': screening_growth,
        'bulk_screening_growth': bulk_screening_growth,
        'job_growth': screening_growth,  # Using screening growth as job growth for now
    }
    
    # Get top skills from resumes
    top_skills = []
    
    # You can add code here to extract and count skills from resumes
    # For now, let's add some placeholder skills
    top_skills = [
        {'name': 'Python', 'count': 15},
        {'name': 'JavaScript', 'count': 12},
        {'name': 'SQL', 'count': 10},
        {'name': 'React', 'count': 8},
        {'name': 'Data Analysis', 'count': 7},
    ]
    
    context = {
        'business_profile': business_profile,
        'subscription_plan': subscription_plan,
        'subscription_active': subscription_active,
        'remaining_resumes': remaining_resumes,
        'resumes_limit': business_profile.resumes_limit,
        'resumes_screened': business_profile.resumes_screened,
        'recent_screenings': recent_screenings,
        'recent_results': recent_results,
        'recent_jobs': recent_screenings,  # Using screenings as jobs for now
        'stats': stats,
        'top_skills': top_skills,
    }
    
    return render(request, 'business/dashboard.html', context)

@login_required
def business_profile_view(request):
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=request.user)
        business_form = BusinessProfileUpdateForm(request.POST, instance=business_profile)
        
        if user_form.is_valid() and business_form.is_valid():
            user_form.save()
            business_form.save()
            messages.success(request, 'Your business profile has been updated successfully!')
            return redirect('business_profile')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        business_form = BusinessProfileUpdateForm(instance=business_profile)
    
    # Get additional subscription data
    remaining_resumes = business_profile.get_remaining_resumes()
    subscription_active = business_profile.is_subscription_active()
    subscription_plan = business_profile.subscription_plan.capitalize()
    
    context = {
        'user_form': user_form,
        'business_form': business_form,
        'business_profile': business_profile,
        'subscription_plan': subscription_plan,
        'subscription_active': subscription_active,
        'remaining_resumes': remaining_resumes,
        'resumes_limit': business_profile.resumes_limit,
        'resumes_screened': business_profile.resumes_screened,
    }
    
    return render(request, 'business/profile.html', context)

@login_required
def Edit_business_profile_view(request):
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=request.user)
        business_form = BusinessProfileUpdateForm(request.POST, instance=business_profile)
        
        if user_form.is_valid() and business_form.is_valid():
            user_form.save()
            business_form.save()
            messages.success(request, 'Your business profile has been updated successfully!')
            return redirect('business_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Initialize forms with current data
        user_form = ProfileUpdateForm(instance=request.user)
        business_form = BusinessProfileUpdateForm(instance=business_profile)
    
    context = {
        'user_form': user_form,
        'business_form': business_form,
        'business_profile': business_profile,
    }
    
    return render(request, 'business/Edit_business_profile.html', context)

def business_signup_view(request):
    """
    Specialized signup view for businesses that pre-selects 'business' user type.
    """
    if request.method == 'POST':
        # Process the form submission using the regular signup view
        return signup(request)
    else:
        # Show user type selection form with business pre-selected
        user_type_form = UserTypeForm(initial={'user_type': 'business'})
        business_form = BusinessSignupForm()
    
    context = {
        'user_type_form': user_type_form,
        'business_form': business_form,
        'is_business_signup': True  # Flag to indicate this is a business signup page
    }
    return render(request, 'registration/signup.html', context)

def analyze_resume_api(request):
    if request.method == 'POST' and 'resume' in request.FILES:
        resume_file = request.FILES['resume']
        job_title = request.POST.get('job_title', '')
        
        try:
            # Use the resume_analyzer to analyze the resume
            analysis_results = analyze_resume(resume_file, job_title)
            
            # Return the results as JSON
            return JsonResponse(analysis_results)
        except Exception as e:
            print("Error analyzing resume:", e)
            # Return a default response
            return JsonResponse({
                'ats_score': 75,
                'format_score': 80,
                'content_score': 70,
                'keywords_score': 65,
                'strengths': [
                    'Well-structured resume format',
                    'Good use of action verbs',
                    'Quantifiable achievements included'
                ],
                'improvements': [
                    'Add more industry-specific keywords',
                    'Include a professional summary',
                    'Expand on technical skills section'
                ],
                'keywords': [
                    {'name': 'Python', 'found': True},
                    {'name': 'Data Analysis', 'found': True},
                    {'name': 'Project Management', 'found': False}
                ]
            })
    
    # If not a POST request or no resume file
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def bulk_screening(request):
    """
    View for business users to upload and analyze multiple resumes
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    # Check subscription status
    remaining_resumes = business_profile.get_remaining_resumes()
    subscription_active = business_profile.is_subscription_active()
    
    if not subscription_active:
        messages.warning(request, 'Your subscription is not active. Please renew your subscription to continue.')
        return redirect('pricing')
    
    if remaining_resumes <= 0:
        messages.warning(request, f'You have reached your limit of {business_profile.resumes_limit} resumes. Please upgrade your plan to continue.')
        return redirect('pricing')
    
    # Initialize context
    context = {
        'business_profile': business_profile,
        'remaining_resumes': remaining_resumes,
        'recent_screenings': []
    }
    
    # Get recent bulk screening sessions
    recent_screenings = BulkResumeScreen.objects.filter(business=business_profile).order_by('-created_at')[:5]
    context['recent_screenings'] = recent_screenings
    
    if request.method == 'POST':
        # Check if it's a bulk upload or job requirements form
        if 'job_title' in request.POST:
            # Process job requirements form
            job_title = request.POST.get('job_title')
            job_description = request.POST.get('job_description')
            required_skills = request.POST.get('required_skills')
            preferred_experience = request.POST.get('preferred_experience', 0)
            
            # Create a new bulk screening session
            bulk_screen = BulkResumeScreen.objects.create(
                business=business_profile,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                preferred_experience=preferred_experience,
                status='pending'
            )
            
            # Store the bulk screen ID in session for future resume uploads
            request.session['current_bulk_screen_id'] = bulk_screen.id
            
            messages.success(request, 'Job requirements saved. Now you can upload resumes for screening.')
            return redirect('bulk_upload_resumes_with_id', bulk_id=bulk_screen.id)
        
    return render(request, 'business/bulk_screening.html', context)

@login_required
def bulk_upload_resumes(request, bulk_id=None):
    """
    View for uploading multiple resumes for a bulk screening session
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    # Get the bulk screening session from either the URL parameter or session
    if bulk_id:
        try:
            bulk_screen = BulkResumeScreen.objects.get(id=bulk_id, business=business_profile)
            # Update session to match the current screening
            request.session['current_bulk_screen_id'] = bulk_id
        except BulkResumeScreen.DoesNotExist:
            messages.error(request, 'Screening session not found.')
            return redirect('bulk_screening')
    else:
        # Get from session if not in URL
        bulk_screen_id = request.session.get('current_bulk_screen_id')
        if not bulk_screen_id:
            messages.error(request, 'No active screening session found. Please start a new screening.')
            return redirect('bulk_screening')
        
        try:
            bulk_screen = BulkResumeScreen.objects.get(id=bulk_screen_id, business=business_profile)
        except BulkResumeScreen.DoesNotExist:
            messages.error(request, 'Screening session not found.')
            return redirect('bulk_screening')
    
    context = {
        'business_profile': business_profile,
        'bulk_screen': bulk_screen,
        'remaining_resumes': business_profile.get_remaining_resumes(),
    }
    
    if request.method == 'POST':
        if 'resumes' in request.FILES:
            files = request.FILES.getlist('resumes')
            resumes_count = len(files)
            
            # Check if user has enough remaining resumes
            if business_profile.get_remaining_resumes() < resumes_count:
                messages.warning(request, f'You only have {business_profile.get_remaining_resumes()} resume(s) left in your plan. Please upgrade to upload more resumes.')
                return redirect('pricing')
            
            bulk_screen.status = 'processing'
            bulk_screen.resumes_count = resumes_count
            bulk_screen.save()
            
            success_count = 0
            error_count = 0
            
            # Process each resume file
            for resume_file in files:
                try:
                    logger.info(f"Processing resume file: {resume_file.name}")
                    
                    # Create a Resume object
                    resume = Resume.objects.create(
                        name=f"Uploaded from {resume_file.name}",
                        email="pending_extraction@example.com",
                        resume_file=resume_file,
                        status='pending'
                    )
                    
                    # Use the new analyze_resume_for_job_direct function
                    analysis_result = analyze_resume_for_job_direct(resume_file, bulk_screen.job_title, bulk_screen.required_skills, request.user)
                    
                    # Create a result entry for this resume
                    result = BulkResumeResult.objects.create(
                        bulk_screen=bulk_screen,
                        resume=resume,
                        match_score=analysis_result.get('match_score', 0),
                        ats_score=analysis_result.get('ats_score', 0),
                        rank=0,  # Will be updated later
                        strengths=analysis_result.get('strengths', ''),
                        weaknesses=analysis_result.get('weaknesses', ''),
                        recommendation=analysis_result.get('recommendation', '')
                    )
                    
                    # Update resume with extracted info
                    resume.name = analysis_result.get('name', resume.name)
                    resume.email = analysis_result.get('email', resume.email)
                    resume.phone = analysis_result.get('phone', '')
                    resume.skills = analysis_result.get('skills', '')
                    resume.experience = analysis_result.get('experience', '')
                    resume.education = analysis_result.get('education', '')
                    
                    # Get predicted role and ranking from Flask API
                    try:
                        from resume_analyzer.utils.resume_parser import ResumeAnalyzer
                        analyzer = ResumeAnalyzer()
                        
                        # Read the file content directly
                        resume_file.seek(0)  # Reset file pointer
                        resume_content = resume_file.read()
                        
                        # Extract text from the content
                        resume_text = analyzer.extract_text_from_content(resume_content)
                        
                        api_url = 'http://localhost:5000/analyze'
                        api_response = requests.post(
                            url=api_url,
                            json={
                                "resume_text": resume_text,
                                "job_title": bulk_screen.job_title,
                            },
                            headers={'Content-Type': 'application/json'},
                            timeout=3
                        ).json()
                        
                        resume.predicted_role = api_response.get('predicted_role', 'Not predicted')
                        resume.ranking = api_response.get('resume_ranking', 'Analyzing...')
                        resume.confidence_score = api_response.get('confidence_score', 75)
                    except Exception as e:
                        logger.error(f"Error getting AI analysis: {str(e)}")
                        resume.predicted_role = 'Not predicted'
                        resume.ranking = 'Analyzing...'
                        resume.confidence_score = 75
                    
                    resume.status = 'reviewed'
                    resume.save()
                    
                    # Update business profile resume count
                    business_profile.resumes_screened += 1
                    business_profile.save()
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing resume {resume_file.name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    error_count += 1
                    
                    try:
                        # Try to get the created resume
                        resume = Resume.objects.filter(name__contains=resume_file.name).first()
                        if resume:
                            resume.status = 'failed'
                            resume.save()
                            
                            # Create a minimal result entry to avoid empty results
                            BulkResumeResult.objects.create(
                                bulk_screen=bulk_screen,
                                resume=resume,
                                match_score=30,
                                ats_score=40,
                                rank=999,  # High rank indicates low priority
                                strengths='Error processing resume',
                                weaknesses=f'File could not be processed: {str(e)}',
                                recommendation='Please upload a different file format'
                            )
                        else:
                            # Create a new resume entry if one wasn't created earlier
                            try:
                                resume = Resume.objects.create(
                                    name=f"Failed: {resume_file.name}",
                                    email="failed@example.com",
                                    resume_file=resume_file,
                                    status='failed'
                                )
                                
                                # Create a minimal result entry
                                BulkResumeResult.objects.create(
                                    bulk_screen=bulk_screen,
                                    resume=resume,
                                    match_score=30,
                                    ats_score=40,
                                    rank=999,
                                    strengths='Error processing resume',
                                    weaknesses=f'File could not be processed: {str(e)}',
                                    recommendation='Please upload a different file format'
                                )
                            except Exception as inner_e:
                                logger.error(f"Critical error creating resume entry: {str(inner_e)}")
                    except Exception as inner_e:
                        logger.error(f"Error updating resume status: {str(inner_e)}")
            
            # Update ranks for all results in this screening
            results = BulkResumeResult.objects.filter(bulk_screen=bulk_screen).order_by('-match_score')
            for i, result in enumerate(results, 1):
                result.rank = i
                result.save()
            
            # Mark bulk screening as completed
            bulk_screen.status = 'completed'
            bulk_screen.completed_at = timezone.now()
            bulk_screen.save()
            
            if error_count > 0:
                messages.warning(request, f'Processed {success_count} resumes successfully with {error_count} errors.')
            else:
                messages.success(request, f'Successfully processed all {resumes_count} resumes.')
            
            return redirect('bulk_screening_results', bulk_id=bulk_screen.id)
        else:
            messages.error(request, 'No resume files were uploaded.')
    
    return render(request, 'business/bulk_upload_resumes.html', context)

@login_required
def bulk_screening_results(request, bulk_id):
    """
    View for displaying the results of a bulk screening
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    try:
        bulk_screen = BulkResumeScreen.objects.get(id=bulk_id, business=business_profile)
    except BulkResumeScreen.DoesNotExist:
        messages.error(request, 'Screening session not found.')
        return redirect('bulk_screening')
    
    # Get only the current screening session's results, ordered by rank
    results = BulkResumeResult.objects.filter(
        bulk_screen=bulk_screen
    ).order_by('rank')
    
    # Calculate metrics for the summary section
    avg_match_score = results.aggregate(Avg('match_score'))['match_score__avg'] or 0
    avg_ats_score = results.aggregate(Avg('ats_score'))['ats_score__avg'] or 0
    top_candidates = [r for r in results if r.match_score >= 70]
    
    context = {
        'business_profile': business_profile,
        'bulk_screen': bulk_screen,
        'results': results,
        'avg_match_score': avg_match_score,
        'avg_ats_score': avg_ats_score,
        'top_candidates': top_candidates,
    }
    
    return render(request, 'business/bulk_screening_results.html', context)

@login_required
def resume_result_api(request, result_id):
    """
    API endpoint for getting details of a specific resume result
    """
    try:
        logger.info(f"Received API request for resume result ID: {result_id}")
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        logger.error("Business profile not found for user")
        return JsonResponse({'error': 'You do not have a business profile.'}, status=403)
    
    try:
        # Get the result and ensure it belongs to the business
        result = BulkResumeResult.objects.get(id=result_id)
        if result.bulk_screen.business != business_profile:
            logger.error(f"Permission denied for result ID {result_id}, requested by {request.user.username}")
            return JsonResponse({'error': 'You do not have permission to view this result.'}, status=403)
    except BulkResumeResult.DoesNotExist:
        logger.error(f"Result not found for ID: {result_id}")
        return JsonResponse({'error': 'Result not found.'}, status=404)

    logger.info(f"Processing resume result for {result.resume.name} (ID: {result.resume.id})")

    # Format the required skills as a list
    required_skills = [skill.strip() for skill in result.bulk_screen.required_skills.split(',')]
    
    # Split strengths and weaknesses by semicolon
    strengths_list = [s.strip() for s in result.strengths.split(';') if s.strip()]
    weaknesses_list = [w.strip() for w in result.weaknesses.split(';') if w.strip()]
    
    # Identify skills in the resume
    resume_skills = [skill.strip() for skill in result.resume.skills.split(',') if skill.strip()]
    
    # Determine which required skills are found in the resume skills
    found_skills = []
    missing_skills = []
    
    for skill in required_skills:
        skill_found = False
        for resume_skill in resume_skills:
            if skill.lower() in resume_skill.lower() or resume_skill.lower() in skill.lower():
                skill_found = True
                break
        
        if skill_found:
            found_skills.append(skill)
        else:
            missing_skills.append(skill)
    
    # Format the experience for display
    experience_list = []
    if result.resume.experience:
        experience_entries = result.resume.experience.split('\n')
        for entry in experience_entries:
            if entry.strip():
                experience_list.append(entry.strip())
    
    # Just get predicted_role and confidence_score from Flask API if possible
    predicted_role = "Not predicted"
    confidence_score = 75
    resume_ranking = "5/10"
    
    try:
        # Only call API for these fields, not for match score
        resume_file = result.resume.resume_file
        if resume_file:
            # Get the file path
            resume_file_path = resume_file.path
            
            try:
                # Use a different approach for extracting text
                from resume_analyzer.utils.resume_parser import ResumeAnalyzer
                
                # Create analyzer and extract text directly from file path
                analyzer = ResumeAnalyzer()
                resume_text = analyzer.extract_text_from_file(resume_file_path)
                
                # Define the API URL manually since settings might not have it
                api_url = 'http://localhost:5000/analyze'
                
                # Call Flask API with timeout to avoid blocking
                api_response = requests.post(
                    url=api_url,
                    json={
                        "resume_text": resume_text,
                        "job_title": result.bulk_screen.job_title,
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=3  # Short timeout to prevent delays
                ).json()
                
                logger.info(f"API Response: {api_response}")
                
                # Get ONLY predicted_role and confidence_score from API
                predicted_role = api_response.get('predicted_role', predicted_role)
                confidence_score = api_response.get('confidence_score', confidence_score)
                resume_ranking = api_response.get('resume_ranking', resume_ranking)
            except Exception as e:
                logger.error(f"Error extracting text or calling API: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting API data: {str(e)}")
    
    # Prepare the response data
    response_data = {
        'id': result.id,
        'resume': {
            'id': result.resume.id,
            'name': result.resume.name,
            'email': result.resume.email,
            'phone': result.resume.phone or 'N/A',
            'skills': resume_skills,
            'experience_text': result.resume.experience,
            'education_text': result.resume.education
        },
        'scores': {
            'match_score': result.match_score,  # Use the match score from database
            'ats_score': result.ats_score,
            'content_score': 75,  # Default value if not available
            'keyword_score': result.match_score  # Match score is effectively the keyword score
        },
        'analysis': {
            'strengths': strengths_list,
            'weaknesses': weaknesses_list,
            'recommendation': result.recommendation,
            'found_skills': found_skills,
            'missing_skills': missing_skills,
            'experience': experience_list
        },
        'job_info': {
            'title': result.bulk_screen.job_title,
            'required_skills': required_skills,
            'preferred_experience': result.bulk_screen.preferred_experience
        },
        # Add AI prediction data
        'ai_analysis': {
            'predicted_role': predicted_role,
            'confidence_score': confidence_score,
            'resume_ranking': resume_ranking
        }
    }
    
    logger.info(f"Sending response for resume result ID: {result_id}")
    return JsonResponse(response_data)

@login_required
def job_portal_integration(request):
    """
    View for integrating with job portals to fetch resumes
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    context = {
        'business_profile': business_profile,
        'supported_portals': [
            {'name': 'LinkedIn', 'status': 'Coming Soon'},
            {'name': 'Indeed', 'status': 'Coming Soon'},
            {'name': 'Monster', 'status': 'Coming Soon'},
            {'name': 'ZipRecruiter', 'status': 'Coming Soon'},
        ]
    }
    
    return render(request, 'business/job_portal_integration.html', context)

@login_required
def export_bulk_results(request, bulk_id):
    """
    View for exporting bulk screening results to CSV
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    try:
        bulk_screen = BulkResumeScreen.objects.get(id=bulk_id, business=business_profile)
    except BulkResumeScreen.DoesNotExist:
        messages.error(request, 'Screening session not found.')
        return redirect('bulk_screening')
    
    # Get all results for this screening, ordered by rank
    results = bulk_screen.results.all().order_by('rank')
    
    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bulk_screening_{bulk_id}.csv"'
    
    writer = csv.writer(response)
    # Write header row
    writer.writerow([
        'Rank', 
        'Name', 
        'Email', 
        'Phone', 
        'Match Score', 
        'ATS Score', 
        'Skills', 
        'Strengths', 
        'Weaknesses', 
        'Recommendations'
    ])
    
    # Write data rows
    for result in results:
        writer.writerow([
            result.rank,
            result.resume.name,
            result.resume.email,
            result.resume.phone or 'N/A',
            f"{result.match_score:.1f}%",
            f"{result.ats_score:.1f}%",
            result.resume.skills,
            result.strengths,
            result.weaknesses,
            result.recommendation
        ])
    
    return response

@login_required
def view_resume(request, resume_id):
    """
    View a single resume with its details
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        messages.error(request, 'You do not have a business profile.')
        return redirect('home')
    
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        messages.error(request, 'Resume not found.')
        return redirect('bulk_screening')
    
    # Get the latest result for this resume if any
    latest_result = BulkResumeResult.objects.filter(resume=resume).order_by('-created_at').first()
    
    context = {
        'business_profile': business_profile,
        'resume': resume,
        'result': latest_result,
    }
    
    return render(request, 'business/resume_detail.html', context)

@login_required
def chat_view(request):
    """
    View for the AI chat assistant
    """
    chat_form = ChatMessageForm()
    
    # Get the user's chat history
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    
    context = {
        'chat_form': chat_form,
        'chat_history': chat_history,
    }
    
    return render(request, 'chat.html', context)

def get_fallback_response(query):
    """
    Provides predefined answers for common questions when OpenAI API is unavailable
    """
    query = query.lower()
    
    # Dictionary of common questions and their answers
    common_qa = {
        "how do i upload a resume": "To upload a resume, click on the 'Upload' button in the navigation menu. You can upload PDF, DOCX, or TXT files. The system will analyze the resume and extract key information.",
        
        "what is ats": "ATS (Applicant Tracking System) is software used by employers to manage job applications. Our system checks if your resume is ATS-friendly and provides suggestions to improve compatibility.",
        
        "how is the match score calculated": "The match score is calculated by comparing the skills, experience, and education in a resume against the job requirements. It considers factors like keyword matching, experience relevance, and skill alignment.",
        
        "how many resumes can i upload": "The number of resumes you can upload depends on your subscription plan. Free users can upload 25 resumes, Standard plan allows 100 resumes, and Premium plan offers unlimited resume uploads.",
        
        "what is bulk screening": "Bulk screening allows business users to upload and analyze multiple resumes at once against a specific job description. Resumes are then ranked by their match with the job requirements.",
        
        "how to interpret the results": "The resume analysis results show extracted skills, experience, education, and an overall match score. It also highlights strengths and weaknesses, and provides recommendations for improvement.",
        
        "what's the difference between match score and ats score": "The match score measures how well a resume matches the job requirements, while the ATS score indicates how likely the resume is to pass through automated applicant tracking systems."
    }
    
    # Check if the query matches or contains any of the common questions
    for question, answer in common_qa.items():
        if question in query:
            return answer
    
    # If no match found, provide a generic response
    return "I'm currently operating in offline mode. For specific help, please try again later when I'm connected to my knowledge base, or contact our support team."

@login_required
@require_POST
def chat_message_api(request):
    """
    API endpoint for sending and receiving chat messages
    """
    # Import our custom chatbot here (local import to avoid circular imports)
    try:
        from .chatbot import ResumeScreeningChatbot
        print("Successfully imported ResumeScreeningChatbot")
    except Exception as e:
        print(f"Error importing chatbot: {str(e)}")
        return JsonResponse({
            'message': "I'm sorry, there was a technical issue loading the chat assistant. Please try again later.",
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        })
    
    # Check if this is a JSON request or form data
    try:
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_message = data.get('message', '')
                if not user_message:
                    return JsonResponse({'error': 'No message provided'}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            # Handle form data (from the full chat page)
            form = ChatMessageForm(request.POST)
            if not form.is_valid():
                return JsonResponse({'error': 'Invalid form data'}, status=400)
            user_message = form.cleaned_data['message']
        
        print(f"Received message: {user_message}")
        
        # Save user message to database
        try:
            ChatMessage.objects.create(
                user=request.user,
                is_user=True,
                message=user_message
            )
            print("User message saved to database")
        except Exception as e:
            print(f"Error saving user message: {str(e)}")
        
        # Initialize our custom NLP chatbot
        try:
            chatbot = ResumeScreeningChatbot()
            print("Chatbot initialized successfully")
        except Exception as e:
            print(f"Error initializing chatbot: {str(e)}")
            return JsonResponse({
                'message': "I'm sorry, there was an error initializing the chat assistant. Please try again later.",
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            })
        
        # Get response from chatbot
        try:
            print("Getting response from chatbot")
            bot_response = chatbot.get_response(user_message)
            print(f"Chatbot response: {bot_response}")
            
            # Check if response is a dictionary (new format) or a string (old format)
            if isinstance(bot_response, dict):
                ai_message = bot_response.get('text', "I'm sorry, I couldn't process that request")
                navigation = bot_response.get('navigation', False)
                destination = bot_response.get('destination', None)
            else:
                # Handle legacy string response
                ai_message = bot_response
                navigation = False
                destination = None
                
                # Check if the legacy response contains a navigation link
                link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', ai_message)
                if link_match:
                    destination = link_match.group(2)
                    # Check if this is a primary navigation response
                    navigation = any(phrase in ai_message for phrase in [
                        "You can access that here",
                        "Navigate to",
                        "I'll take you to",
                        "Go to"
                    ])
            
            # Save AI response to database
            try:
                ChatMessage.objects.create(
                    user=request.user,
                    is_user=False,
                    message=ai_message
                )
                print("AI response saved to database")
            except Exception as e:
                print(f"Error saving AI response: {str(e)}")
            
            # Return response with navigation information if available
            return JsonResponse({
                'message': ai_message,
                'timestamp': timezone.now().isoformat(),
                'navigation': navigation,
                'destination': destination
            })
            
        except Exception as e:
            print(f"Error getting chatbot response: {str(e)}")
            
            # Generate a basic error response
            fallback_response = "I'm sorry, I encountered an error while processing your request. Please try again later or use the navigation buttons above."
            
            # Save fallback response to database
            try:
                ChatMessage.objects.create(
                    user=request.user,
                    is_user=False,
                    message=fallback_response
                )
            except Exception as db_error:
                print(f"Error saving fallback response: {str(db_error)}")
            
            return JsonResponse({
                'message': fallback_response,
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            })
    
    except Exception as outer_error:
        print(f"Critical error in chat_message_api: {str(outer_error)}")
        return JsonResponse({
            'message': "I'm sorry, there was a critical error in processing your message. Please try again later.",
            'timestamp': timezone.now().isoformat(),
            'error': str(outer_error)
        })

@login_required
def clear_chat_history(request):
    """
    Clears all chat history for the current user
    """
    if request.method == "POST":
        ChatMessage.objects.filter(user=request.user).delete()
        messages.success(request, "Chat history cleared successfully.")
    
    return redirect('chat')

@login_required
def chat_history_api(request):
    """
    API endpoint to get chat history for the sidebar
    """
    # Get the user's chat history (last 10 messages)
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Reverse the order to get oldest first
    chat_history = reversed(list(chat_history))
    
    # Format and return the messages
    messages = []
    for message in chat_history:
        messages.append({
            'content': message.message,
            'is_user': message.is_user,
            'timestamp': message.created_at.isoformat()
        })
    
    return JsonResponse({'messages': messages})

@login_required
def chat_job_recommendation(request):
    """
    API endpoint for getting job recommendations based on user's resume skills
    """
    from .chatbot import JobRecommendationEngine
    
    # Get the user's latest resume if one exists
    user_resume = None
    try:
        # Check if user has any resume
        if hasattr(request.user, 'resumes'):
            user_resume = request.user.resumes.order_by('-created_at').first()
    except:
        pass
    
    # If no resume found, return an error
    if not user_resume:
        return JsonResponse({
            'error': 'No resume found. Please upload a resume to get job recommendations.',
            'timestamp': timezone.now().isoformat()
        })
    
    # Get skills from the resume (assuming they're stored as a comma-separated string)
    skills = []
    if hasattr(user_resume, 'skills') and user_resume.skills:
        skills = [skill.strip() for skill in user_resume.skills.split(',')]
    
    # Initialize the recommendation engine
    recommendation_engine = JobRecommendationEngine()
    
    # Get job recommendations
    job_recommendations = recommendation_engine.recommend_jobs(skills)
    
    # Format the response
    if job_recommendations:
        response_message = "Based on your resume skills, you might be a good fit for these roles:\n\n"
        for i, job in enumerate(job_recommendations, 1):
            response_message += f"{i}. {job}\n"
        response_message += "\nWould you like more information about any of these roles?"
    else:
        response_message = "I couldn't find specific job recommendations based on your current resume. Consider adding more skills to your resume for better recommendations."
    
    # Save the response as a chat message
    ChatMessage.objects.create(
        user=request.user,
        is_user=False,
        message=response_message
    )
    
    return JsonResponse({
        'message': response_message,
        'jobs': job_recommendations,
        'timestamp': timezone.now().isoformat()
    })

@login_required
def chat_resume_improvement(request):
    """
    API endpoint for getting resume improvement suggestions
    """
    from .chatbot import ResumeImprovement
    
    # Areas to improve can be passed in the request or determined automatically
    areas_to_improve = request.GET.getlist('areas', [])
    
    # Initialize the resume improvement engine
    improvement_engine = ResumeImprovement()
    
    # Get improvement suggestions
    suggestions = improvement_engine.get_suggestions(areas_to_improve)
    
    # Format the response
    response_message = "Here are some suggestions to improve your resume:\n\n"
    for i, suggestion in enumerate(suggestions, 1):
        response_message += f"{i}. {suggestion}\n\n"
    
    # Save the response as a chat message
    ChatMessage.objects.create(
        user=request.user,
        is_user=False,
        message=response_message
    )
    
    return JsonResponse({
        'message': response_message,
        'suggestions': suggestions,
        'timestamp': timezone.now().isoformat()
    })

@login_required
def resume_list(request):
    """
    View for listing all resumes uploaded by the user
    """
    # Try to determine if the user is a business user
    is_business_user = False
    
    try:
        # Check if user has a business profile
        business_profile = request.user.business_profile
        is_business_user = True
        
        # For business users, we'll show all resumes analyzed in bulk screenings
        resume_results = BulkResumeResult.objects.filter(
            bulk_screen__business=business_profile
        ).select_related('resume', 'bulk_screen').order_by('-created_at')
        
        context = {
            'is_business_user': is_business_user,
            'business_profile': business_profile,
            'resume_results': resume_results,
            'title': 'All Analyzed Resumes'
        }
        
        return render(request, 'business/resume_list.html', context)
        
    except BusinessProfile.DoesNotExist:
        # Not a business user, continue to regular user flow
        pass
    
    # For regular users, show their individual resume analyses
    try:
        user_profile = request.user.user_profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(
            user=request.user,
            subscription_plan='free',
            resumes_limit=25
        )
    
    # Get all resume analyses for this user
    analyses = ResumeAnalysis.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'is_business_user': is_business_user,
        'user_profile': user_profile,
        'analyses': analyses,
        'title': 'My Resume Analyses'
    }
    
    # Redirect to the dashboard instead which shows the resume list
    return redirect('dashboard')

@login_required
def get_resume_analysis(request, result_id):
    """
    API endpoint to get detailed analysis for a single resume result
    in a format similar to analyze_resume_api
    """
    try:
        business_profile = request.user.business_profile
    except BusinessProfile.DoesNotExist:
        return JsonResponse({'error': 'You do not have a business profile.'}, status=403)
    
    try:
        # Get the result and ensure it belongs to the business
        result = BulkResumeResult.objects.get(id=result_id)
        if result.bulk_screen.business != business_profile:
            return JsonResponse({'error': 'You do not have permission to view this result.'}, status=403)
    except BulkResumeResult.DoesNotExist:
        return JsonResponse({'error': 'Result not found.'}, status=404)
    
    resume = result.resume
    
    # Format the results like analyze_resume_api
    analysis_results = {
        'success': True,
        'ats_score': result.ats_score,
        'job_match_score': result.match_score,
        'resume_ranking': f"{result.rank}/10" if result.rank <= 10 else f"{result.rank}",
        'confidence_score': 85,  # Default value
        'predicted_role': resume.predicted_role if hasattr(resume, 'predicted_role') else "Not predicted",
        'candidate_name': resume.name,
        'email': resume.email,
        'phone': resume.phone or 'Not provided',
        'analysis': {
            'content_score': 70,  # Default content score
            'keywords_score': result.match_score,
            'strengths': result.strengths.split(';') if result.strengths else [],
            'improvements': result.weaknesses.split(';') if result.weaknesses else [],
            'keywords': [],
            'experience': [resume.experience] if resume.experience else []
        }
    }
    
    # Extract skills and create keywords list
    if resume.skills:
        skills = [skill.strip() for skill in resume.skills.split(',')]
        keywords = []
        for skill in skills:
            keywords.append({'name': skill, 'found': True})
        analysis_results['analysis']['keywords'] = keywords
    
    return JsonResponse(analysis_results)


