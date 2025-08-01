import re
import random
import string
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import WordNetLemmatizer
import logging

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download necessary NLTK data (uncomment these lines when first running)
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('omw-1.4')

class ResumeScreeningChatbot:
    """
    A custom NLP-based chatbot that can answer questions about the resume screening tool.
    Uses basic NLP techniques to provide responses without relying on external APIs.
    """
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        
        # Create a corpus of potential questions and their responses
        self.responses = {
            "greeting": [
                "Hello! How can I help you with your resume screening today?",
                "Hi there! Welcome to the Resume Screening Tool. What can I assist you with?",
                "Greetings! I'm your resume assistant. How may I help you?"
            ],
            "goodbye": [
                "Goodbye! Feel free to return if you have more questions.",
                "Thanks for chatting. Have a great day!",
                "Bye! Good luck with your job search!"
            ],
            "thanks": [
                "You're welcome!",
                "Happy to help!",
                "My pleasure. Is there anything else you need help with?"
            ],
            "upload_resume": [
                "To upload your resume, click on the 'Upload Resume' button in the navigation menu or use this link: [Upload Resume](/upload/)",
                "You can upload your resume by navigating to the upload page: [Upload Resume](/upload/)"
            ],
            "ats_explanation": [
                "ATS (Applicant Tracking System) is software used by employers to manage job applications. Our system checks if your resume is ATS-friendly and provides suggestions to improve compatibility.",
                "An ATS or Applicant Tracking System is software that employers use to filter and sort resumes. We analyze how well your resume would perform in these systems and suggest improvements."
            ],
            "match_score": [
                "The match score is calculated by comparing the skills, experience, and education in your resume against the job requirements. It considers factors like keyword matching, experience relevance, and skill alignment.",
                "Our match score algorithm analyzes your resume against job requirements, considering keywords, skills, experience level, and education to generate a percentage match."
            ],
            "resume_limit": [
                "The number of resumes you can upload depends on your subscription plan. Free users can upload 25 resumes, Standard plan allows 100 resumes, and Premium plan offers unlimited resume uploads.",
                "Your resume upload limit is based on your current plan. Free: 25 resumes, Standard: 100 resumes, Premium: unlimited resumes."
            ],
            "bulk_screening": [
                "Bulk screening allows business users to upload and analyze multiple resumes at once against a specific job description. You can access this feature here: [Bulk Screening](/business/bulk-screening/)",
                "Business users can use bulk screening to process multiple resumes simultaneously against a job description. Access it here: [Bulk Screening](/business/bulk-screening/)"
            ],
            "results_interpretation": [
                "The resume analysis results show extracted skills, experience, education, and an overall match score. It also highlights strengths and weaknesses, and provides recommendations for improvement.",
                "Our analysis results include your ATS compatibility score, skills assessment, keyword matches, and specific recommendations to improve your resume."
            ],
            "score_difference": [
                "The match score measures how well your resume matches specific job requirements, while the ATS score indicates how likely your resume is to pass through automated applicant tracking systems.",
                "Match score is job-specific, showing how well you match a particular position. ATS score is a general measure of how well your resume will perform in automated screening systems."
            ],
            "upgrade_account": [
                "To upgrade your account, go to the Pricing page: [Pricing](/pricing/) and select a plan that suits your needs. You can pay securely online and your account will be upgraded immediately.",
                "Visit the Pricing section to view our different plans: [Pricing](/pricing/) - Click on 'Upgrade Now' under your preferred plan to enhance your account features."
            ],
            "business_features": [
                "Business users get access to bulk resume screening, candidate ranking, analytics dashboards, team collaboration tools, and API integration options. Learn more here: [Business Features](/about/)",
                "Our business plans include features like bulk resume processing, detailed analytics, custom scoring algorithms, and team management capabilities. Upgrade here: [Upgrade](/business/signup/)"
            ],
            "dashboard": [
                "You can access your dashboard here: [Dashboard](/dashboard/) to view your resume analysis results, track your progress, and manage your account.",
                "Go to your dashboard: [Dashboard](/dashboard/) to see all your resume analyses and account information."
            ],
            "profile": [
                "You can view and edit your profile here: [Profile](/profile/) to update your personal information and account settings.",
                "Access your profile settings here: [Profile](/profile/) to manage your account details."
            ],
            "contact_support": [
                "If you need assistance, you can contact our support team here: [Contact](/contact/) and we'll be happy to help you.",
                "For any questions or issues, please reach out through our contact page: [Contact](/contact/)"
            ],
            "pricing": [
                "You can view our pricing plans here: [Pricing](/pricing/) to choose the best option for your needs.",
                "Check out our different subscription tiers here: [Pricing](/pricing/)"
            ],
            "login": [
                "You can log in to your account here: [Login](/login/)",
                "Access your account by logging in here: [Login](/login/)"
            ],
            "signup": [
                "Create a new account here: [Sign Up](/signup/)",
                "Register for a new account here: [Sign Up](/signup/)"
            ],
            "navigation": [
                "Here are the main pages you can visit:\n- [Home](/)\n- [Upload Resume](/upload/)\n- [Dashboard](/dashboard/)\n- [Profile](/profile/)\n- [Pricing](/pricing/)\n- [Contact](/contact/)",
                "You can navigate to these pages:\n- [Home](/)\n- [Upload Resume](/upload/)\n- [Dashboard](/dashboard/)\n- [Pricing](/pricing/)\n- [Contact](/contact/)"
            ],
            "fallback": [
                "I'm not sure I understand. Could you rephrase your question? Or you can navigate to our main pages: [Home](/) | [Dashboard](/dashboard/) | [Upload Resume](/upload/)",
                "I don't have that information right now. You might find what you need on our [Home](/) page or [Dashboard](/dashboard/).",
                "I'm still learning. Would you like to go to our [Upload Resume](/upload/) page or [Contact Support](/contact/)?"
            ]
        }
        
        # Define navigation intents for routing users to specific pages
        self.navigation_routes = {
            "upload_resume": "/upload/",
            "dashboard": "/dashboard/",
            "profile": "/profile/",
            "contact_support": "/contact/",
            "pricing": "/pricing/",
            "login": "/login/",
            "signup": "/signup/",
            "bulk_screening": "/business/bulk-screening/",
            "business_dashboard": "/business/dashboard/",
            "home": "/"
        }
        
        # Prepare the data for TF-IDF
        self.prepare_data()
    
    def prepare_data(self):
        """Prepare the training data for the chatbot"""
        try:
            self.training_data = []
            self.training_labels = []
            
            # Add training data for each response category
            self.add_training_data("hello|hi|hey|greetings", "greeting")
            self.add_training_data("bye|goodbye|see you|later", "goodbye")
            self.add_training_data("thanks|thank you|appreciate", "thanks")
            self.add_training_data("upload|submit|send resume|file|document", "upload_resume")
            self.add_training_data("what is ats|applicant tracking|ats mean|ats system", "ats_explanation")
            self.add_training_data("match score|calculate|score work|how score|percentage match", "match_score")
            self.add_training_data("how many resume|resume limit|upload limit|maximum resume", "resume_limit")
            self.add_training_data("bulk screening|multiple resume|many resume|batch|group", "bulk_screening")
            self.add_training_data("interpret result|read result|understand result|analysis mean", "results_interpretation")
            self.add_training_data("difference between match|ats score|score differ|two score", "score_difference")
            self.add_training_data("upgrade account|premium|paid plan|subscription|better plan", "upgrade_account")
            self.add_training_data("business feature|company|enterprise|corporate|team feature", "business_features")
            self.add_training_data("dashboard|my account|my resume|account page", "dashboard")
            self.add_training_data("profile|my profile|account setting|personal info", "profile")
            self.add_training_data("contact|help|support|assistance|question", "contact_support")
            self.add_training_data("price|cost|plan|subscription cost|how much", "pricing")
            self.add_training_data("login|sign in|access account|enter account", "login")
            self.add_training_data("signup|register|create account|new account|join", "signup")
            self.add_training_data("navigate|menu|page|section|where is|how to find|go to", "navigation")
            
            print(f"Prepared {len(self.training_data)} training examples")
            
            # Make sure we have training data before creating the vectorizer
            if not self.training_data:
                print("Warning: No training data available for TF-IDF!")
                self.tfidf_matrix = None
                self.X_train = []
                self.y_train = []
                return
            
            # Initialize TF-IDF vectorizer with simple parameters
            self.vectorizer = TfidfVectorizer(analyzer='word', lowercase=True)
            
            try:
                # Fit the vectorizer with training data
                self.tfidf_matrix = self.vectorizer.fit_transform(self.training_data)
                # Set X_train to the TF-IDF matrix and y_train to the labels
                self.X_train = self.tfidf_matrix
                self.y_train = self.training_labels
                print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
            except Exception as e:
                print(f"Error in vectorizer fitting: {str(e)}")
                self.tfidf_matrix = None
                self.X_train = []
                self.y_train = []
        except Exception as e:
            print(f"Error in prepare_data: {str(e)}")
            self.tfidf_matrix = None
            self.X_train = []
            self.y_train = []
    
    def add_training_data(self, pattern, label):
        """Add training data based on patterns and their corresponding labels"""
        for word in pattern.split('|'):
            self.training_data.append(word.strip())
            self.training_labels.append(label)
    
    def preprocess_text(self, text):
        """Preprocess the user's message"""
        try:
            # Convert to lowercase and remove extra whitespace
            text = text.lower().strip()
            
            # Simple approach - just handle basic punctuation and split on space
            # This is more robust than using NLTK tokenization which can fail
            text = text.replace('.', ' ').replace(',', ' ').replace('!', ' ').replace('?', ' ')
            text = text.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace(';', ' ')
            text = text.replace('\n', ' ').replace('\t', ' ')
            
            # Remove multiple spaces
            while '  ' in text:
                text = text.replace('  ', ' ')
            
            return text
        except Exception as e:
            print(f"Error in text preprocessing: {str(e)}")
            # If preprocessing fails, return the original text or a simplified version
            return text.lower().strip()
    
    def get_response(self, user_message):
        """
        Get a response to the user's message.
        """
        try:
            # Preprocess the user message
            processed_message = self.preprocess_text(user_message)
            print(f"Processed message: '{processed_message}'")
            
            # Check for direct navigation or known intents first
            navigation_response = self.check_navigation_intent(user_message)
            if navigation_response:
                print("Navigation intent detected")
                return navigation_response
            
            # If we don't have a vectorizer, return default response
            if not hasattr(self, 'vectorizer') or self.vectorizer is None:
                print("No vectorizer available")
                return "I'm not fully trained yet. Please try basic questions or use the navigation buttons."
            
            # Check if we have any training data
            if not hasattr(self, 'X_train') or self.X_train is None:
                print("X_train is not initialized")
                return "I don't have any training data yet. Please ask the administrator to train me."
                
            # Check if X_train is a sparse matrix and has data
            if hasattr(self.X_train, 'shape') and self.X_train.shape[0] == 0:
                print(f"X_train shape: {self.X_train.shape} (empty)")
                return "I don't have any training data yet. Please ask the administrator to train me."
                
            # Check if y_train is properly populated
            if not hasattr(self, 'y_train') or not self.y_train:
                print("y_train is empty")
                return "I don't have any training labels. Please ask the administrator to train me."
            
            print(f"X_train shape: {self.X_train.shape}, y_train length: {len(self.y_train)}")
            
            # Try to vectorize the input
            try:
                # Transform user input
                user_input_vector = self.vectorizer.transform([processed_message])
                print(f"User input vector shape: {user_input_vector.shape}")
                
                # Calculate cosine similarity between user input and training data
                cosine_similarities = cosine_similarity(user_input_vector, self.X_train)
                
                # Get index of highest similarity
                most_similar_idx = cosine_similarities.argmax()
                
                # Get similarity score
                similarity_score = cosine_similarities[0, most_similar_idx]
                print(f"Best match index: {most_similar_idx}, similarity score: {similarity_score}")
                print(f"Best matching training example: '{self.training_data[most_similar_idx]}'")
                
                # If similarity is below threshold, return default message
                if similarity_score < 0.3:
                    print(f"Similarity score {similarity_score} below threshold (0.3)")
                    return "I'm not sure I understand. Could you phrase your question differently? Or use the navigation buttons to go to a specific page."
                
                # Get the intent of the most similar example
                matched_intent = self.y_train[most_similar_idx]
                print(f"Matched intent: '{matched_intent}'")
                
                # Return response based on intent
                return self.get_intent_response(matched_intent, user_message)
            except Exception as e:
                logger.error(f"Error in vector similarity calculation: {str(e)}")
                return "I'm having trouble processing your request right now. Please try again with simpler language or use the navigation buttons."
            
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return "Sorry, I encountered an error. Please try again or use the navigation buttons above."

    def check_navigation_intent(self, user_message):
        """
        Check if user is directly asking for navigation to a specific page
        """
        try:
            # Dictionary mapping intents to URLs/responses
            intent_urls = {
                'homepage': '/',
                'home': '/',
                'dashboard': '/dashboard/',
                'upload': '/upload/',
                'resume upload': '/upload/',
                'upload resume': '/upload/',
                'view resumes': '/view_resumes/',
                'resumes': '/view_resumes/',
                'analyzed resumes': '/view_resumes/',
                'my profile': '/profile/',
                'profile': '/profile/',
                'help': '/help/',
                'info': '/help/',
                'login': '/login/',
                'logout': '/logout/',
                'register': '/register/',
                'signup': '/register/'
            }
            
            # Common navigation patterns
            nav_patterns = [
                r'take me to (.*)',
                r'go to (.*)',
                r'navigate to (.*)',
                r'show me (.*)',
                r'open (.*)',
                r'access (.*)',
                r'how do i get to (.*)',
                r'i want to see (.*)',
                r'bring me to (.*)'
            ]
            
            # Check for direct intent mentions first
            lower_message = user_message.lower().strip()
            
            # Check for simple direct matches (e.g., "home", "dashboard")
            for intent, url in intent_urls.items():
                # Full match (e.g., "home" or "go to home")
                pattern = r'\b' + re.escape(intent) + r'\b'
                if re.search(pattern, lower_message):
                    # Create a response with a link
                    page_name = intent.replace('_', ' ').title()
                    return {
                        'text': f"I'll take you to the {page_name} page.",
                        'navigation': True,
                        'destination': url
                    }
            
            # Check for navigation patterns
            for pattern in nav_patterns:
                match = re.search(pattern, lower_message)
                if match:
                    target = match.group(1).strip().lower()
                    # Check if the target matches any of our intents
                    for intent, url in intent_urls.items():
                        if target == intent or target in intent.split():
                            page_name = intent.replace('_', ' ').title()
                            return {
                                'text': f"I'll take you to the {page_name} page.",
                                'navigation': True,
                                'destination': url
                            }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in check_navigation_intent: {str(e)}")
            return None

    def get_intent_response(self, intent, original_message=None):
        """
        Get a response based on the detected intent
        """
        try:
            # Debug: Print the matched intent
            print(f"Matched intent: {intent}")
            
            # Map intents to response functions
            intent_responses = {
                'greeting': self.greeting_response,
                'goodbye': self.goodbye_response,
                'upload_resume': self.upload_resume_response,
                'view_resumes': self.view_resumes_response,
                'profile': self.profile_response,
                'help': self.help_response,
                'resume_analysis': self.resume_analysis_response,
                'about': self.about_response,
                'thanks': self.thanks_response,
                'features': self.features_response,
                'ats_explanation': lambda x: random.choice(self.responses["ats_explanation"]),
                'match_score': lambda x: random.choice(self.responses["match_score"]),
                'resume_limit': lambda x: random.choice(self.responses["resume_limit"]),
                'bulk_screening': lambda x: random.choice(self.responses["bulk_screening"]),
                'results_interpretation': lambda x: random.choice(self.responses["results_interpretation"]),
                'score_difference': lambda x: random.choice(self.responses["score_difference"]),
                'upgrade_account': lambda x: random.choice(self.responses["upgrade_account"]),
                'business_features': lambda x: random.choice(self.responses["business_features"]),
                'dashboard': lambda x: random.choice(self.responses["dashboard"]),
                'contact_support': lambda x: random.choice(self.responses["contact_support"]),
                'pricing': lambda x: random.choice(self.responses["pricing"]),
                'login': lambda x: random.choice(self.responses["login"]),
                'signup': lambda x: random.choice(self.responses["signup"]),
                'navigation': lambda x: random.choice(self.responses["navigation"])
            }
            
            # Get the response function for the intent
            response_func = intent_responses.get(intent, None)
            
            if response_func:
                # Call the response function
                response = response_func(original_message)
                
                # Check if response is already in the new format
                if isinstance(response, dict) and 'text' in response:
                    return response
                
                # Otherwise convert to new format
                return {'text': response}
            else:
                # Fallback response for unknown intents
                logger.warning(f"No response function for intent: {intent}")
                return {
                    'text': "I'm not sure how to respond to that. Please try another question or use the navigation buttons above."
                }
            
        except Exception as e:
            logger.error(f"Error in get_intent_response: {str(e)}")
            return {
                'text': "I encountered an error processing your request. Please try again or use the navigation buttons."
            }

    # Response functions for different intents
    def greeting_response(self, original_message=None):
        """Generate a greeting response"""
        greetings = [
            "Hello! How can I help you with resume screening today?",
            "Hi there! I can help you upload, view, or analyze resumes. What would you like to do?",
            "Welcome! I'm your resume screening assistant. How can I assist you today?",
            "Hello! I'm here to help with your resume screening needs. What would you like to do?"
        ]
        return random.choice(greetings)

    def goodbye_response(self, original_message=None):
        """Generate a goodbye response"""
        goodbyes = [
            "Goodbye! Come back if you need help with resume screening.",
            "See you later! Feel free to return if you have more questions.",
            "Farewell! I'm here whenever you need assistance with resumes.",
            "Take care! I'll be here if you need more help with resume screening."
        ]
        return random.choice(goodbyes)

    def upload_resume_response(self, original_message=None):
        """Information about uploading resumes"""
        return {
            'text': "You can upload a resume for analysis on the Upload page. I'll take you there!",
            'navigation': True,
            'destination': '/upload/'
        }

    def view_resumes_response(self, original_message=None):
        """Information about viewing resumes"""
        return {
            'text': "You can view your analyzed resumes on the Resumes page. Let me take you there!",
            'navigation': True,
            'destination': '/view_resumes/'
        }

    def profile_response(self, original_message=None):
        """Information about user profile"""
        return {
            'text': "You can view and edit your profile settings on the Profile page. Here you go!",
            'navigation': True,
            'destination': '/profile/'
        }

    def help_response(self, original_message=None):
        """General help information"""
        help_text = "Here are some things I can help you with:\n\n"
        help_text += "- Upload and analyze resumes\n"
        help_text += "- View analyzed resumes\n"
        help_text += "- Update your profile\n"
        help_text += "- Navigate around the application\n\n"
        help_text += "You can also use the buttons above to quickly navigate to different sections."
        
        return help_text

    def resume_analysis_response(self, original_message=None):
        """Information about resume analysis"""
        return "Our system analyzes resumes to extract key information like skills, experience, and education. To analyze a resume, first upload it on the [Upload page](/upload/)."

    def about_response(self, original_message=None):
        """Information about the application"""
        return "This is a resume screening application that helps you analyze, organize, and review resumes efficiently. It uses NLP to extract key information from resumes and provides insights to help with hiring decisions."

    def thanks_response(self, original_message=None):
        """Response to thank you messages"""
        thanks_responses = [
            "You're welcome! Happy to help.",
            "No problem at all! Is there anything else you need?",
            "You're welcome! Feel free to ask if you need more assistance.",
            "Glad I could help! Let me know if you need anything else."
        ]
        return random.choice(thanks_responses)

    def features_response(self, original_message=None):
        """Information about application features"""
        return "Our resume screening application offers several features:\n\n- Resume uploading and analysis\n- Skill extraction and matching\n- Experience validation\n- Education verification\n- Resume organization and filtering\n\nYou can access these features from the [Dashboard](/dashboard/)."

# Additional features to enhance the chatbot's capabilities

class JobRecommendationEngine:
    """
    A simple recommendation engine that suggests job titles based on skills
    """
    def __init__(self):
        # Sample job titles and their required skills
        self.job_skill_mapping = {
            "Software Developer": ["python", "java", "javascript", "sql", "git", "algorithms"],
            "Data Scientist": ["python", "r", "statistics", "machine learning", "sql", "data visualization"],
            "Web Developer": ["html", "css", "javascript", "react", "node.js", "php"],
            "Project Manager": ["project management", "leadership", "communication", "budgeting", "scrum", "agile"],
            "UX Designer": ["user research", "wireframing", "prototyping", "ui design", "figma", "adobe xd"],
            "DevOps Engineer": ["linux", "aws", "docker", "kubernetes", "ci/cd", "automation"],
            "Marketing Specialist": ["social media", "content creation", "seo", "analytics", "marketing strategy"],
            "Sales Representative": ["negotiation", "communication", "crm", "sales strategy", "lead generation"]
        }
    
    def recommend_jobs(self, skills):
        """
        Recommend job titles based on the skills provided
        """
        skills = [skill.lower() for skill in skills]
        job_scores = {}
        
        for job, required_skills in self.job_skill_mapping.items():
            matching_skills = sum(1 for skill in skills if any(skill in req_skill for req_skill in required_skills))
            job_scores[job] = matching_skills / len(required_skills)
        
        # Sort jobs by score in descending order
        sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3 matching jobs
        return [job for job, score in sorted_jobs[:3] if score > 0.2]

class ResumeImprovement:
    """
    Provides suggestions to improve resumes based on analysis
    """
    def __init__(self):
        # Common resume improvement suggestions
        self.suggestions = {
            "action_verbs": "Use powerful action verbs (achieved, improved, led) at the beginning of bullet points. For examples and to test your resume, go to: [Upload Resume](/upload/)",
            "quantifiable_results": "Include numbers and percentages to quantify your achievements. Get a detailed analysis here: [Upload Resume](/upload/)",
            "keywords": "Incorporate industry-specific keywords that match job descriptions. Our ATS scanner can help: [Upload Resume](/upload/)",
            "formatting": "Use a clean, consistent format with clear section headings. Check your formatting score: [Upload Resume](/upload/)",
            "skills_section": "Include a dedicated skills section with relevant technical and soft skills. Analyze your skills: [Upload Resume](/upload/)",
            "education": "List education in reverse chronological order with relevant details. See how employers view your education section: [Upload Resume](/upload/)",
            "contact_info": "Ensure your contact information is up-to-date and professional. Update in your [Profile](/profile/)",
            "professional_summary": "Add a concise professional summary highlighting your value proposition. Get feedback: [Upload Resume](/upload/)"
        }
    
    def get_suggestions(self, areas_to_improve):
        """
        Get specific improvement suggestions based on areas that need improvement
        """
        if not areas_to_improve:
            # Return general suggestions if no specific areas are provided
            return [
                "Upload your resume to get personalized improvement suggestions: [Upload Resume](/upload/)",
                "View your resume analytics on your dashboard: [Dashboard](/dashboard/)",
                "For more detailed resume help, please contact our support team: [Contact](/contact/)"
            ]
        
        # Return specific suggestions for the areas to improve
        return [self.suggestions[area] for area in areas_to_improve if area in self.suggestions]

# Example usage:
# chatbot = ResumeScreeningChatbot()
# response = chatbot.get_response("How do I upload my resume?")
# print(response) 