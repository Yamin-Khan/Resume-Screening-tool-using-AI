import requests
from django.conf import settings
from resume_analyzer.analyzer import analyze_resume as nlp_analyze_resume

class ResumeAIService:
    def __init__(self):
        self.base_url = getattr(settings, 'RESUME_AI_SERVICE_URL', 'http://localhost:5000')
    
    def analyze_resume(self, resume_text, job_title=None):
        """
        Send resume to AI service for analysis
        """
        try:
            # First try the Flask service
            response = requests.post(
                f"{self.base_url}/analyze",
                json={
                    'resume_text': resume_text,
                    'job_title': job_title
                }
            )
            response.raise_for_status()
            flask_analysis = response.json()
            
            # Then get NLP analysis
            nlp_analysis = nlp_analyze_resume(resume_text, job_title)
            
            # Combine both analyses
            return {
                'flask_analysis': flask_analysis,
                'nlp_analysis': nlp_analysis
            }
        except requests.exceptions.RequestException as e:
            print(f"Error calling AI service: {str(e)}")
            # Fallback to NLP analysis only
            return {
                'flask_analysis': None,
                'nlp_analysis': nlp_analyze_resume(resume_text, job_title)
            }

    def get_match_score(self, resume_text, job_title, job_description):
        """
        Get detailed match score from AI service
        """
        try:
            # First try the Flask service
            response = requests.post(
                f"{self.base_url}/match_score",
                json={
                    'resume_text': resume_text,
                    'job_title': job_title,
                    'job_description': job_description
                }
            )
            response.raise_for_status()
            flask_score = response.json()
            
            # Then get NLP analysis
            nlp_score = nlp_analyze_resume(resume_text, job_title)
            
            # Combine both scores
            return {
                'predicted_role': flask_score.get('predicted_role', 'Not Available'),
                'confidence_score': flask_score.get('confidence_score', nlp_score.get('match_score', 0)),
                'resume_ranking': flask_score.get('resume_ranking', 'Not Available'),
                'nlp_analysis': nlp_score
            }
        except requests.exceptions.RequestException as e:
            print(f"Error getting match score: {str(e)}")
            # Fallback to NLP analysis only
            nlp_score = nlp_analyze_resume(resume_text, job_title)
            return {
                'predicted_role': 'Not Available',
                'confidence_score': nlp_score.get('match_score', 0),
                'resume_ranking': 'Not Available',
                'nlp_analysis': nlp_score
            } 