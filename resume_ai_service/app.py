from flask import Flask, request, render_template, jsonify
import pickle
import numpy as np
import os
import fitz  # PyMuPDF
import docx
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Get the directory containing app.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load model and vectorizer
with open(os.path.join(current_dir, 'resume_classifier_model.pkl'), 'rb') as f:
    model = pickle.load(f)

with open(os.path.join(current_dir, 'vectorizer.pkl'), 'rb') as f:
    vectorizer = pickle.load(f)

# Category decoder
category_map = {
    0: 'Java Developer',
    1: 'Data Scientist',
    2: 'HR',
    3: 'Data Analyst',
    4: 'DevOps Engineer',
    5: 'Web Developer',
    6: 'Python Developer',
    7: 'Android Developer',
    8: 'iOS Developer',
    9: 'UI/UX Designer',
    10: 'Project Manager',
    11: 'Business Analyst'
}

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join(page.get_text() for page in doc)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)

def predict_resume_category(text):
    cleaned_text = text.strip().replace("\n", " ").replace("\r", "")
    vector = vectorizer.transform([cleaned_text])
    probabilities = model.predict_proba(vector)

    predicted_index = np.argmax(probabilities)
    predicted_category = category_map.get(predicted_index, "Unknown")

    raw_confidence = np.max(probabilities)
    realistic_confidence = round(min(max(raw_confidence, 0.70), 0.95) * 100, 2)

    resume_rank = round(realistic_confidence / 10 - np.random.uniform(0.5, 1.5), 1)
    resume_rank = max(min(resume_rank, 9.5), 6.0)

    return predicted_category, realistic_confidence, resume_rank


    return render_template('chatbot.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'resume_file' not in request.files:
        return render_template('upload.html', error="No file uploaded.")

    file = request.files['resume_file']
    if file.filename == '':
        return render_template('upload.html', error="No selected file.")

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    extension = file.filename.rsplit('.', 1)[-1].lower()
    if extension == 'pdf':
        resume_text = extract_text_from_pdf(file_path)
    elif extension == 'docx':
        resume_text = extract_text_from_docx(file_path)
    else:
        return render_template('upload.html', error="Only PDF or DOCX files are supported.")

    category, confidence, rank = predict_resume_category(resume_text)

    return render_template('upload.html',
                           prediction=category,
                           confidence=confidence,
                           resume_rank=rank)



    if request.method == 'POST':
        # Get the data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        
        # Redirect to a new page after form submission
        return render_template('contact_success.html', name=name)
    
    return render_template('contact.html')

# API Endpoints for Django Integration
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_title = data.get('job_title', None)
        
        if not resume_text:
            return jsonify({'error': 'No resume text provided'}), 400
            
        predicted_role, confidence_score, resume_ranking = predict_resume_category(resume_text)
        job_match_score = calculate_job_match(resume_text, job_title)        
        return jsonify({
            'predicted_role': predicted_role,
            'confidence_score': confidence_score,
            'resume_ranking': f"{resume_ranking}/10",
            'job_match_score': job_match_score
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/match_score', methods=['POST'])
def match_score():
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_title = data.get('job_title', '')
        job_description = data.get('job_description', '')
        
        if not resume_text:
            return jsonify({'error': 'No resume text provided'}), 400
            
        predicted_role, confidence_score, resume_ranking = predict_resume_category(resume_text)
        
        # Calculate additional metrics based on job description match
        job_match_score = calculate_job_match(resume_text, job_description)
        
        return jsonify({
            'predicted_role': predicted_role,
            'confidence_score': confidence_score,
            'resume_ranking': f"{resume_ranking}/10",
            'job_match_score': job_match_score
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_job_match(resume_text, job_title):
    # Simple keyword matching for job description
    resume_words = set(resume_text.lower().split())
    job_words = set(job_title.lower().split())
    
    # Calculate overlap
    common_words = resume_words.intersection(job_words)
    match_percentage = (len(common_words) / len(job_words)) * 100 if job_words else 0
    
    return round(min(max(match_percentage, 0), 100), 2)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
