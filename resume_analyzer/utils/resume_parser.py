import spacy
import json
import os
import re
import PyPDF2
import docx
import docx2txt
from typing import Dict, Any, List, Optional
from io import StringIO

class ResumeAnalyzer:
    def __init__(self):
        """Initialize the ResumeAnalyzer."""
        # Initialize spaCy model if available
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
            print("Warning: spaCy model not found. Run 'python -m spacy download en_core_web_sm' to install it.")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file formats."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_extension == '.txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            print(f"Error extracting text from file: {str(e)}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            text = docx2txt.process(file_path)
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files."""
        try:
            # Try different encodings in order of likelihood
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try reading as bytes and decoding with error handling
            with open(file_path, 'rb') as file:
                content = file.read()
                return content.decode('utf-8', errors='replace')
                
        except Exception as e:
            print(f"Error extracting text from TXT: {str(e)}")
            return ""
    
    def extract_text_from_content(self, content: bytes) -> str:
        """Extract text content from file content directly."""
        try:
            # Create a temporary file to process the content
            import tempfile
            import os
            
            # Get file extension from content type or default to .txt
            file_extension = '.txt'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Use the existing extract_text_from_file method
                text = self.extract_text_from_file(temp_file_path)
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            return text if text else "Failed to extract text from content"
            
        except Exception as e:
            print(f"Error extracting text from content: {str(e)}")
            return "Document could not be processed. Please check file format."
    
    def parse_resume(self, file_path: str, job_title: str = '', industry: str = '') -> Dict[str, Any]:
        """
        Parse and analyze a resume file using traditional NLP techniques.
        
        Args:
            file_path: Path to the resume file
            job_title: Optional job title for targeted analysis
            industry: Optional industry for targeted analysis
            
        Returns:
            Dictionary containing parsed resume data and analysis
        """
        try:
            # Extract text from file
            resume_text = self.extract_text_from_file(file_path)
            
            # Extract basic information
            basic_info = self._extract_basic_info(resume_text)
            
            # Extract skills
            skills = self.extract_skills(resume_text)
            
            # Calculate scores
            ats_score = self.calculate_ats_score(resume_text)
            format_score = self.calculate_format_score(resume_text)
            content_score = self.calculate_content_score(resume_text)
            keywords_score = self.calculate_keywords_score(resume_text)
            
            # Identify strengths and improvements
            strengths = self.identify_strengths(resume_text)
            improvements = self.identify_improvements(resume_text)
            
            # Extract important keywords
            keywords = self.extract_important_keywords(resume_text)
            
            # Extract experience
            experience = self.extract_experience(resume_text)
            
            return {
                'ats_score': ats_score,
                'content_score': content_score,
                'keywords_score': keywords_score,
                'strengths': strengths,
                'improvements': improvements,
                'keywords': keywords,
                'experience': [experience] if experience else []
            }
            
        except Exception as e:
            print(f"Error parsing resume: {str(e)}")
            return {
                'ats_score': 70,
                'content_score': 65,
                'keywords_score': 60,
                'strengths': ['Resume has a clear structure'],
                'improvements': ['Consider adding more specific details'],
                'keywords': [{'name': 'Basic Skills', 'found': True}],
                'experience': []
            }
    
    def calculate_ats_score(self, text: str) -> int:
        """Calculate ATS compatibility score based on resume content."""
        score = 70  # Base score
        
        # Check for section headers
        headers = ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']
        found_headers = sum(1 for header in headers if re.search(r'\b' + re.escape(header) + r'\b', text.lower()))
        
        if found_headers >= 4:
            score += 15
        elif found_headers >= 2:
            score += 10
        
        # Check for consistent formatting
        if re.search(r'\n\n', text):
            score += 5
        
        # Check for contact information
        if self.extract_email(text) and self.extract_phone(text):
            score += 10
        
        return min(score, 100)
    
    def calculate_format_score(self, text: str) -> int:
        """Calculate format score based on resume layout and organization."""
        score = 75  # Base score
        
        # Check for section headers
        headers = ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']
        found_headers = sum(1 for header in headers if re.search(r'\b' + re.escape(header) + r'\b', text.lower()))
        
        if found_headers >= 4:
            score += 15
        elif found_headers >= 2:
            score += 10
        
        # Check for consistent formatting
        if re.search(r'\n\n', text):
            score += 5
        
        return min(score, 100)
    
    def calculate_content_score(self, text: str) -> int:
        """Calculate content quality score."""
        score = 70  # Base score
        
        # Check for action verbs
        action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed', 'led', 'achieved',
                       'improved', 'increased', 'reduced', 'negotiated', 'collaborated', 'coordinated']
        found_verbs = sum(1 for verb in action_verbs if re.search(r'\b' + re.escape(verb) + r'\b', text.lower()))
        
        if found_verbs >= 5:
            score += 15
        elif found_verbs >= 3:
            score += 10
        
        # Check for quantifiable achievements
        if re.search(r'\b\d+%\b', text):
            score += 10
        
        return min(score, 100)
    
    def calculate_keywords_score(self, text: str) -> int:
        """Calculate keyword relevance score."""
        skills = self.extract_skills(text)
        
        if len(skills) > 15:
            return 90
        elif len(skills) > 10:
            return 80
        elif len(skills) > 5:
            return 70
        elif len(skills) > 3:
            return 60
        return 50
    
    def identify_strengths(self, text: str) -> List[str]:
        """Identify resume strengths."""
        strengths = []
        
        skills = self.extract_skills(text)
        if len(skills) > 5:
            strengths.append("Good variety of skills listed")
        
        # Check for quantifiable achievements
        if re.search(r'\b\d+%\b', text):
            strengths.append("Includes quantifiable achievements")
        
        # Check for action verbs
        action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed', 'led', 'achieved']
        found_verbs = sum(1 for verb in action_verbs if re.search(r'\b' + re.escape(verb) + r'\b', text.lower()))
        if found_verbs >= 3:
            strengths.append("Good use of action verbs")
        
        # Check for contact information
        if self.extract_email(text) and self.extract_phone(text):
            strengths.append("Complete contact information")
        
        return strengths or ["Resume has a clear structure"]
    
    def identify_improvements(self, text: str) -> List[str]:
        """Identify areas for improvement in the resume."""
        improvements = []
        
        # Check for contact information
        if not self.extract_email(text):
            improvements.append("Add email address")
        if not self.extract_phone(text):
            improvements.append("Add phone number")
        
        # Check for education
        if not self.extract_education(text):
            improvements.append("Add education details")
        
        # Check for experience
        if not self.extract_experience(text):
            improvements.append("Add work experience details")
        
        # Check for skills
        skills = self.extract_skills(text)
        if len(skills) < 5:
            improvements.append("Add more skills to your resume")
        
        return improvements or ["Consider adding more specific details"]
    
    def extract_important_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extract important keywords and indicate if they're found."""
        important_keywords = ['python', 'java', 'javascript', 'html', 'css', 'react', 'leadership']
        
        results = []
        for keyword in important_keywords:
            found = bool(re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()))
            results.append({'name': keyword.title(), 'found': found})
        
        return results
    
    def extract_experience(self, text: str) -> str:
        """Extract work experience information from resume text."""
        experience_keywords = ['experience', 'work history', 'employment', 'professional experience']
        
        for keyword in experience_keywords:
            pattern = re.compile(r'(?i)' + re.escape(keyword) + r'.*?(?:\n\n|\Z)', re.DOTALL)
            match = pattern.search(text)
            if match:
                experience_section = match.group(0)
                return experience_section[:100] + "..." if len(experience_section) > 100 else experience_section
        
        return ""
    
    def extract_education(self, text: str) -> str:
        """Extract education information from resume text."""
        education_keywords = ['education', 'academic', 'qualification', 'degree']
        
        for keyword in education_keywords:
            pattern = re.compile(r'(?i)' + re.escape(keyword) + r'.*?(?:\n\n|\Z)', re.DOTALL)
            match = pattern.search(text)
            if match:
                education_section = match.group(0)
                return education_section[:100] + "..." if len(education_section) > 100 else education_section
        
        return ""
    
    def extract_name(self, text: str) -> str:
        """Extract name from resume text."""
        lines = text.split('\n')
        for line in lines[:10]:  # Look in the first 10 lines
            line = line.strip()
            if line and len(line.split()) <= 5 and not re.search(r'@|http|www|resume|cv', line.lower()):
                return line
        return "Unknown"
    
    def extract_email(self, text: str) -> str:
        """Extract email from resume text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)
        return ""
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number from resume text."""
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
            r'\b\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # +1 123 456 7890
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text."""
        skill_keywords = [
            'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue', 'node',
            'django', 'flask', 'fastapi', 'spring', 'express', 'postgresql', 'mysql', 'mongodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'github', 'gitlab', 'jenkins',
            'ci/cd', 'agile', 'scrum', 'kanban', 'jira', 'confluence', 'excel', 'word', 'powerpoint',
            'photoshop', 'illustrator', 'figma', 'sketch', 'adobe', 'leadership', 'communication',
            'teamwork', 'problem-solving', 'critical thinking', 'project management', 'time management',
            'data analysis', 'data science', 'machine learning', 'ai', 'artificial intelligence', 'nlp',
            'natural language processing', 'computer vision', 'deep learning', 'tensorflow', 'pytorch',
            'keras', 'scikit-learn', 'pandas', 'numpy', 'r', 'tableau', 'power bi', 'excel', 'sql',
            'linux', 'windows', 'macos', 'troubleshooting', 'networking', 'security', 'firewall',
            'vpn', 'encryption', 'backup', 'recovery', 'automation', 'scripting', 'shell', 'bash',
            'powershell', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin', 'swift',
            'objective-c', 'mobile', 'android', 'ios', 'flutter', 'react native', 'xamarin', 'ionic',
            'api', 'rest', 'graphql', 'soap', 'json', 'xml', 'yaml', 'markdown', 'html5', 'css3',
            'sass', 'less', 'bootstrap', 'material ui', 'tailwind', 'jquery', 'typescript'
        ]
        
        found_skills = []
        for skill in skill_keywords:
            if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
                found_skills.append(skill.title())
        
        return found_skills
    
    def _extract_basic_info(self, text: str) -> Dict[str, str]:
        """Extract basic information from resume text."""
        return {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text)
        }

# Helper functions for external use

def extract_text_from_resume(resume_file):
    """Extract text from a resume file object."""
    # If the resume_file is a file path, use the ResumeAnalyzer
    if isinstance(resume_file, str):
        analyzer = ResumeAnalyzer()
        return analyzer.extract_text_from_file(resume_file)
    
    # If it's a file object (Django UploadedFile), extract text based on file type
    try:
        file_name = resume_file.name
        file_extension = file_name.lower().split('.')[-1]
        
        # Save the file temporarily to process it
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            for chunk in resume_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Process the file based on its extension
        try:
            analyzer = ResumeAnalyzer()
            text = analyzer.extract_text_from_file(temp_file_path)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return text if text else "Failed to extract text from resume"
        
    except Exception as e:
        print(f"Error extracting text from resume: {str(e)}")
        return "Document could not be processed. Please check file format."

def extract_basic_info(text):
    """Extract basic information from resume text."""
    analyzer = ResumeAnalyzer()
    return {
        'name': analyzer.extract_name(text),
        'email': analyzer.extract_email(text),
        'phone': analyzer.extract_phone(text)
    }

def extract_skills(text):
    """Extract skills from resume text."""
    analyzer = ResumeAnalyzer()
    return analyzer.extract_skills(text) 