from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from .utils.resume_parser import ResumeAnalyzer, extract_text_from_resume
from .models import ResumeAnalysis
import os
import tempfile
import requests
from typing import Dict, Any

# Initialize the analyzer
analyzer = ResumeAnalyzer()

@require_http_methods(["POST"])
def analyze_resume(request) -> JsonResponse:
    """
    API endpoint for analyzing uploaded resumes.
    
    Expected POST data:
    - resume: File upload
    - job_title: Optional job title for targeted analysis
    - industry: Optional industry for targeted analysis
    """
    print("<<<<<<<<<<<<<API called for resume>>>>>>>>>>>>")
    if 'resume' not in request.FILES:
        return JsonResponse({'error': 'No resume file provided'}, status=400)
        
    resume_file = request.FILES['resume']
    job_title = request.POST.get('job_title', '')
    industry = request.POST.get('industry', '')
    resume_text = extract_text_from_resume(resume_file)
    api_response = requests.post(
        url='http://localhost:5000/analyze',
        json={
            "resume_text": resume_text,
            "job_title": job_title,
        },
        headers={'Content-Type': 'application/json'}
    ).json()
    # Create a temporary file to store the uploaded resume
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as temp_file:
        for chunk in resume_file.chunks():
            temp_file.write(chunk)
        temp_path = temp_file.name
            
    try:
        # Analyze the resume
        analysis = analyzer.parse_resume(temp_path, job_title, industry)
        
        print(api_response)
        # Prepare the response data
        response_data = {
            'success': True,
            'ats_score': analysis['ats_score'],
            'analysis': {
                'content_score': analysis['content_score'],
                'keywords_score': analysis['keywords_score'],
                'strengths': analysis['strengths'],
                'improvements': analysis['improvements'],
                'keywords': analysis['keywords'],
                'experience': analysis['experience']
            },
            "predicted_role": api_response.get("predicted_role"),
            "confidence_score": api_response.get("confidence_score"),
            "resume_ranking": api_response.get("resume_ranking"),
            "job_match_score": api_response.get("job_match_score"),
            'saved': request.user.is_authenticated
        }
        
        # Save analysis if user is authenticated
        if request.user.is_authenticated:
            # Save the resume file
            saved_file = resume_file  # We'll use the original file for storage
            
            # Create a new ResumeAnalysis record
            resume_analysis = ResumeAnalysis(
                user=request.user,
                resume_file=saved_file,
                file_name=resume_file.name,
                job_title=job_title,
                industry=industry,
                ats_score=analysis['ats_score'],
                analysis_data=analysis
            )
            resume_analysis.save()
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error analyzing resume: {str(e)}")
        return JsonResponse({
            'error': 'Failed to analyze resume',
            'details': str(e)
        }, status=500)
        
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass


def user_resume_list(request):
    """View to display user's resume analysis history."""
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html', {'redirect_to': 'user_resume_list'})
    
    analyses = ResumeAnalysis.objects.filter(user=request.user)
    return render(request, 'resume_analyzer/user_resume_list.html', {'analyses': analyses})


def resume_detail(request, analysis_id):
    """View to display detailed resume analysis results."""
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html', {'redirect_to': 'resume_detail', 'analysis_id': analysis_id})
    
    analysis = ResumeAnalysis.objects.get(id=analysis_id, user=request.user)
    return render(request, 'resume_analyzer/resume_detail.html', {'analysis': analysis})

