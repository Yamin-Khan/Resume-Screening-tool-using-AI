import os
import tempfile
import requests
from resume_analyzer.utils.resume_parser import ResumeAnalyzer, extract_text_from_resume
import json
from django.http import JsonResponse
import logging
from django.views.decorators.http import require_http_methods
import re

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the analyzer
analyzer = ResumeAnalyzer()
@require_http_methods(["POST"])
def analyze_resume_for_job(request) -> JsonResponse:    
    """
    Analyze a resume file for job match.
    
    Args:
        resume_file: The uploaded resume file
        job_title: The job title
        job_description: The job description
        required_skills: The required skills for the job
        
    Returns:
        Dictionary containing analysis results
    """
    resume_file = request.FILES['resume']
    job_title = request.POST.get('job_title', '')
    required_skills = request.POST.get('required_skills', '')
    try:
        # Extract text from resume
        resume_text = extract_text_from_resume(resume_file)
        
        # Call Flask API for additional analysis
        try:
            api_response = requests.post(
                url='http://localhost:5000/analyze',
                json={
                    "resume_text": resume_text,
                    "job_title": job_title,
                },
                headers={'Content-Type': 'application/json'},  # Set a timeout to prevent long waits
            ).json()

            print(api_response)
            # Create a temporary file to store the uploaded resume
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as temp_file:
                for chunk in resume_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
                    
                # Analyze the resume
                analysis = analyzer.parse_resume(temp_path, job_title, required_skills)
                
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
            return JsonResponse(response_data)
            
        except (requests.RequestException, ValueError) as e:
            print(f"Error calling Flask API: {str(e)}")
            api_response = {
                "predicted_role": "Not available",
                "confidence_score": 70,
                "resume_ranking": "5/10",
                "job_match_score": 65
            }
        
        # Save file temporarily to process with ResumeAnalyzer
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as temp_file:
            for chunk in resume_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        try:
            # Use ResumeAnalyzer to parse the resume
            analysis = analyzer.parse_resume(temp_path, job_title)
            
            # Extract contact information
            name = analysis.get('name', '')
            email = analysis.get('email', '')
            phone = analysis.get('phone', '')
            
            # Extract skills as a comma-separated string
            skills = ', '.join(analysis.get('skills', []))
            
            # Format strengths and weaknesses as strings
            strengths = '; '.join(analysis.get('strengths', []))
            weaknesses = '; '.join(analysis.get('improvements', []))
            
            # Calculate match score based on required skills
            required_skills_list = [skill.strip().lower() for skill in required_skills.split(',')]
            found_skills = [skill.lower() for skill in analysis.get('skills', [])]
            
            # Calculate skill match percentage
            skill_matches = sum(1 for skill in required_skills_list if any(s in skill or skill in s for s in found_skills))
            
            # Calculate match score - this was missing before!
            if len(required_skills_list) > 0:
                match_score = (skill_matches / len(required_skills_list)) * 100
            else:
                match_score = 70  # Default if no required skills specified
            
            # Get ATS score from analysis or API
            ats_score = analysis.get('ats_score', 70)
            
            # Format experience and education
            experience = '\n'.join(analysis.get('experience', []))
            education = '\n'.join(analysis.get('education', []))
            
            # Create a recommendation based on match score (now match_score is defined)
            if match_score >= 80:
                recommendation = "Strong match for the position. Recommend immediate interview."
            elif match_score >= 60:
                recommendation = "Good candidate with relevant skills. Consider for interview."
            else:
                recommendation = "Limited match with required skills. May not be suitable for this role."
                
            # Use API values if available
            match_score = api_response.get('job_match_score', match_score)
                
            # Prepare final result
            result = {
                'name': name if name else f"Candidate {os.path.basename(resume_file.name)}",
                'email': email if email else "No email found",
                'phone': phone,
                'skills': skills,
                'match_score': match_score,
                'ats_score': ats_score,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'experience': experience,
                'education': education,
                'recommendation': recommendation,
                'content_score': analysis.get('content_score', 65),
                'predicted_role': api_response.get('predicted_role', 'Not predicted'),
                'confidence_score': api_response.get('confidence_score', 75),
                'resume_ranking': api_response.get('resume_ranking', '5/10'),
            }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        print(f"Error in analyze_resume_for_job: {str(e)}")
        # Return basic fallback data
        return {
            'name': f"Error Processing {os.path.basename(resume_file.name)}",
            'email': "processing-error@example.com",
            'phone': "",
            'skills': "",
            'match_score': 30,
            'ats_score': 40,
            'strengths': "Error processing file",
            'weaknesses': f"Could not extract data: {str(e)}",
            'experience': "",
            'education': "",
            'recommendation': "Please review manually or upload a different format",
            'content_score': 0,
        } 

def analyze_resume_for_job_direct(resume_file, job_title, required_skills, user=None):
    """
    Direct parameter version of analyze_resume_for_job.
    
    Args:
        resume_file: The uploaded resume file
        job_title: The job title
        required_skills: The required skills for the job
        user: Optional user for authentication checks
        
    Returns:
        Dictionary containing analysis results
    """
    temp_path = None
    try:
        # Extract text from resume
        resume_text = extract_text_from_resume(resume_file)
        
        # Make sure we have the text before proceeding
        if not resume_text or len(resume_text.strip()) < 50:
            logger.warning(f"Resume text extraction failed or text too short: {len(resume_text)}")
        
        # Save file temporarily to process with ResumeAnalyzer
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1])
        try:
            # Reset file pointer to beginning
            resume_file.seek(0)
            
            # Write chunks to temp file
            for chunk in resume_file.chunks():
                temp_file.write(chunk)
                
            # Close file explicitly before further operations
            temp_file.close()
            temp_path = temp_file.name
            
            # Now use the analyzer on the temporary file
            analysis = analyzer.parse_resume(temp_path, job_title)
            
            # Extract contact information from the analysis
            name = analysis.get('name', '')
            email = analysis.get('email', '')
            
            # If email not found in analysis, try regex on resume text
            if not email:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_match = re.search(email_pattern, resume_text)
                if email_match:
                    email = email_match.group(0)
            
            phone = analysis.get('phone', '')
            
            # Extract skills from analysis
            skills_from_analysis = analysis.get('skills', [])
            
            # If still no skills, try extracting from resume text directly
            if not skills_from_analysis:
                # Common technical skills to look for
                common_skills = [
                    'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'node.js', 
                    'django', 'flask', 'php', 'ruby', 'c++', 'c#', 'sql', 'nosql', 'mongodb',
                    'aws', 'azure', 'docker', 'kubernetes', 'git', 'jenkins', 'ci/cd', 'agile',
                    'scrum', 'machine learning', 'data analysis', 'excel', 'tableau', 'power bi',
                    'project management', 'leadership', 'communication'
                ]
                
                # Check for each skill in the resume text
                found_skills = []
                for skill in common_skills:
                    if re.search(r'\b' + re.escape(skill) + r'\b', resume_text.lower()):
                        found_skills.append(skill.capitalize())
                
                skills_from_analysis = found_skills
            
            # Format skills as a comma-separated string
            skills = ', '.join(skills_from_analysis)
            
            # Format strengths and weaknesses as strings
            strengths = '; '.join(analysis.get('strengths', []))
            weaknesses = '; '.join(analysis.get('improvements', []))
            
            # Calculate match score based on required skills - THIS IS THE KEY PART
            required_skills_list = [skill.strip().lower() for skill in required_skills.split(',')]
            found_skills = [skill.lower() for skill in skills_from_analysis]
            
            # Calculate skill match percentage
            skill_matches = sum(1 for skill in required_skills_list if any(s in skill or skill in s for s in found_skills))
            
            # Calculate match score
            if len(required_skills_list) > 0:
                match_score = (skill_matches / len(required_skills_list)) * 100
            else:
                match_score = 70  # Default if no required skills specified
            
            # Format experience and education
            experience = '\n'.join(analysis.get('experience', []))
            education = '\n'.join(analysis.get('education', []))
            
            # Create a recommendation based on match score
            if match_score >= 80:
                recommendation = "Strong match for the position. Recommend immediate interview."
            elif match_score >= 60:
                recommendation = "Good candidate with relevant skills. Consider for interview."
            else:
                recommendation = "Limited match with required skills. May not be suitable for this role."
            
            # Call Flask API only for predicted role and confidence score
            api_response = {}
            try:
                api_response = requests.post(
                    url='http://localhost:5000/analyze',
                    json={
                        "resume_text": resume_text,
                        "job_title": job_title,
                    },
                    headers={'Content-Type': 'application/json'},
                    timeout=3  # Add timeout to prevent hanging
                ).json()
                
                logger.info(f"API Response: {api_response}")
            except (requests.RequestException, ValueError) as e:
                logger.error(f"Error calling Flask API: {str(e)}")
                # Initialize default API response if request fails
                api_response = {
                    "predicted_role": "Not available",
                    "confidence_score": 70,
                    "resume_ranking": "5/10",
                }
            
            # Prepare final result - USING LOCAL MATCH SCORE, NOT API
            result = {
                'name': name if name else f"Candidate {os.path.basename(resume_file.name)}",
                'email': email if email else "No email found",
                'phone': phone,
                'skills': skills,
                'match_score': match_score,  # Using our calculated match score
                'job_match_score': match_score,  # For compatibility
                'ats_score': analysis.get('ats_score', 70),
                'strengths': strengths,
                'weaknesses': weaknesses,
                'experience': experience,
                'education': education,
                'recommendation': recommendation,
                'content_score': analysis.get('content_score', 65),
                'predicted_role': api_response.get('predicted_role', 'Not predicted'),
                'confidence_score': api_response.get('confidence_score', 75),
                'resume_ranking': api_response.get('resume_ranking', '5/10'),
            }
            
            return result
            
        finally:
            # Clean up temporary file
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Error deleting temporary file: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in analyze_resume_for_job_direct: {str(e)}")
        # Return basic fallback data
        return {
            'name': f"Error Processing {os.path.basename(resume_file.name)}",
            'email': "processing-error@example.com",
            'phone': "",
            'skills': "",
            'match_score': 30,
            'job_match_score': 30,
            'ats_score': 40,
            'strengths': "Error processing file",
            'weaknesses': f"Could not extract data: {str(e)}",
            'experience': "",
            'education': "",
            'recommendation': "Please review manually or upload a different format",
            'content_score': 0,
            'predicted_role': "Error - Could not predict",
            'confidence_score': 0,
        } 