# # -------------------------------
# # Main Flask application for AI Resume Screener
# # -------------------------------
# from nlp_extractor import extract_skills, _extract_text_from_pdf, _extract_text_from_docx
# from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
# from werkzeug.utils import secure_filename
# from datetime import datetime
# from bson import ObjectId
# import os
# import pymongo
# from pathlib import Path
# from docx import Document
# # Import your existing AI modules
# from semantic_match import compute_similarity
# from skill_gap import detect_skill_gaps
# from llm import analyze_section
# from fpdf import FPDF
# import os
# # -------------------------------
# # Flask & MongoDB setup
# # -------------------------------
# # app = Flask(__name__)
# # app.secret_key = "supersecretkey"

# # db = client["ai_resume_screener"]
# app = Flask(__name__)
# print("Creating Flask app")
# app.secret_key = "supersecretkey"

# MONGO_URI = os.environ.get("MONGO_URI")
# # print("MONGO_URI =", os.environ.get("MONGO_URI"))

# client = pymongo.MongoClient(
#     MONGO_URI,
#     serverSelectionTimeoutMS=5000
# )

# client.admin.command("ping")
# print("MongoDB Connected")
# print("Reached after MongoDB")

# db = client["ai_resume_screener"]
# students = db["students"]
# hr = db["hr"]
# jd_collection = db['job_descriptions']
# applications = db["applications"]

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# REPORT_FOLDER = os.path.join(BASE_DIR, "reports")

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(REPORT_FOLDER, exist_ok=True)

# # -------------------------------
# # Landing Page
# # -------------------------------
# @app.route('/')
# def home():
#     return render_template('index.html')

# # -------------------------------
# # Student Authentication
# # -------------------------------
# @app.route('/student_signup', methods=['GET', 'POST'])
# def student_signup():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email'].strip().lower()
#         password = request.form['password']
#         students.insert_one({'name': name, 'email': email, 'password': password})
#         return redirect(url_for('student_login'))
#     return render_template('student_signup.html')


# @app.route('/student_login', methods=['GET', 'POST'])
# def student_login():
#     if request.method == 'POST':
#         email = request.form['email'].strip().lower()
#         password = request.form['password']
#         user = students.find_one({'email': email})
#         if user and user['password'] == password:
#             session['student_id'] = str(user['_id'])
#             return redirect(url_for('student_dashboard'))
#         return render_template('student_login.html', error="Invalid credentials")
#     return render_template('student_login.html')

# # -------------------------------
# # HR Authentication
# # -------------------------------
# @app.route('/hr_signup', methods=['GET', 'POST'])
# def hr_signup():
#     if request.method == 'POST':
#         email = request.form['email'].strip().lower()
#         password = request.form['password']
#         result = hr.insert_one({'email': email, 'password': password})
#         session['hr_id'] = str(result.inserted_id)
#         return redirect(url_for('hr_dashboard'))
#     return render_template('hr_signup.html')


# @app.route('/hr_login', methods=['GET', 'POST'])
# def hr_login():
#     if request.method == 'POST':
#         email = request.form['email'].strip().lower()
#         password = request.form['password']
#         user = hr.find_one({'email': email})
#         if user and user['password'] == password:
#             session['hr_id'] = str(user['_id'])
#             return redirect(url_for('hr_dashboard'))
#         return render_template('hr_login.html', error="Invalid credentials")
#     return render_template('hr_login.html')

# # -------------------------------
# # Student Dashboard
# # -------------------------------
# @app.route('/student_dashboard')
# def student_dashboard():
#     if 'student_id' not in session:
#         return redirect(url_for('student_login'))
#     student_id = session['student_id']
#     apps = list(applications.find({'student_id': student_id}))
#     return render_template('student_dashboard.html', applications=apps)

# # -------------------------------
# # Resume Upload & AI Processing
# # -------------------------------
# @app.route('/upload_resume', methods=['POST'])
# def upload_resume():
#     if 'student_id' not in session:
#         return redirect(url_for('student_login'))

#     file = request.files['resume']
#     filename = secure_filename(file.filename)
#     resume_path = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(resume_path)

#     # ✅ Detect file type and extract text
#     if filename.lower().endswith(".pdf"):
#         resume_text = _extract_text_from_pdf(Path(resume_path))
#     elif filename.lower().endswith(".docx"):
#         resume_text = _extract_text_from_docx(resume_path)
#     else:
#         return "Unsupported file format", 400

#     # ✅ Load JD text from DB (fallback if empty)
#     jd_doc = jd_collection.find_one() or {}
#     jd_text = jd_doc.get("jd_text", "Generic job description text")

#     # Run AI modules
#     skills_result = extract_skills(resume_text, jd_text)
#     resume_skills = skills_result["resume_skills"]
#     jd_skills = skills_result["jd_skills"]

#     similarity_score = compute_similarity(resume_text, jd_text)
#     gap_report = detect_skill_gaps(resume_text, jd_text)
#     section_feedback = analyze_section(resume_skills, jd_text)

#     # Save report
#     report_filename = f"report_{filename}.txt"
#     report_path = os.path.join(REPORT_FOLDER, report_filename)
#     matched_skills = [skill for skill in resume_skills if skill in jd_skills]
#     missing_skills = [skill for skill in jd_skills if skill not in resume_skills]
#     with open(report_path, "w", encoding="utf-8") as f:
#         f.write("AI Resume Report\n")
#         f.write(f"Score: {section_feedback.avg_score}\n")
#         f.write(f"Matched Skills: {jd_skills}\n")
#         f.write(f"Missing Skills: {[g.skill for g in gap_report.hard_gaps]}\n")
#         for fb in section_feedback.bullets:
#             f.write(f"- {fb.bullet} | Score {fb.score} | Suggestion: {fb.suggestion}\n")

#     applications.insert_one({
#         'student_id': session['student_id'],
#         'resume_filename': filename,
#         'report_filename': report_filename,
#         'status': 'Pending',
#         'created_at': datetime.now()
#     })

#     flash("✅ Resume submitted successfully!")
#     return redirect(url_for('student_dashboard'))

# # -------------------------------
# # HR Dashboard
# # -------------------------------
# @app.route('/hr_dashboard')
# def hr_dashboard():
#     if 'hr_id' not in session:
#         return redirect(url_for('hr_login'))

#     apps = list(applications.find())
#     for app in apps:
#         student = students.find_one({'_id': ObjectId(app['student_id'])})
#         app['student_name'] = student['name'] if student else 'Unknown'

#     jd_doc = jd_collection.find_one() or {}
#     current_jd = jd_doc.get("jd_text", "")

#     return render_template('hr_dashboard.html', applications=apps, current_jd=current_jd)

# # -------------------------------
# # JD Update
# # -------------------------------
# @app.route('/set_jd', methods=['POST'])
# def set_jd():
#     if 'hr_id' not in session:
#         return redirect(url_for('hr_login'))

#     jd_text = request.form['jd_text']
#     jd_collection.update_one({}, {"$set": {"jd_text": jd_text}}, upsert=True)

#     flash("✅ Job Description updated successfully!")
#     return redirect(url_for('hr_dashboard'))

# # -------------------------------
# # Application Detail Page
# # -------------------------------
# @app.route('/application/<id>')
# def application_detail(id):
#     app_data = applications.find_one({'_id': ObjectId(id)})
#     if not app_data:
#         return "Application not found", 404
#     return render_template('application.html', app=app_data)

# # -------------------------------
# # Serve Files
# # -------------------------------
# @app.route('/view_resume/<filename>')
# def view_resume(filename):
#     return send_file(os.path.join(UPLOAD_FOLDER, filename))

# @app.route('/view_report/<filename>')
# def view_report(filename):
#     txt_path = os.path.join(REPORT_FOLDER, filename)
#     if not os.path.exists(txt_path):
#         return "Report not found", 404

#     # ✅ Read the text report
#     with open(txt_path, "r", encoding="utf-8") as f:
#         report_text = f.read()

#     # ✅ Create a PDF
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)

#     for line in report_text.splitlines():
#         pdf.multi_cell(0, 10, line)

#     # ✅ Save temporary PDF
#     pdf_filename = filename.replace(".txt", ".pdf")
#     pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
#     pdf.output(pdf_path)

#     # ✅ Send PDF for download
#     return send_file(pdf_path, as_attachment=True)
    
# @app.route('/set_jd_page')
# def set_jd_page():
#     if 'hr_id' not in session:
#         return redirect(url_for('hr_login'))
#     return render_template('set_jd.html')

# @app.route('/save_jd', methods=['POST'])
# def save_jd():
#     if 'hr_id' not in session:
#         return redirect(url_for('hr_login'))

#     jd_data = {
#         "skills": request.form['skills'],
#         "technologies": request.form['technologies'],
#         "experience": request.form['experience'],
#         "soft_skills": request.form['soft_skills']
#     }

#     jd_collection.update_one({}, {"$set": jd_data}, upsert=True)
#     flash("✅ Job Description saved successfully!")
#     return redirect(url_for('hr_dashboard'))

# # -------------------------------
# # Logout
# # -------------------------------
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('home'))

# # -------------------------------
# # Run app
# # -------------------------------
# if __name__ == "__main__":
#     # Read the port dynamically from Render, default to 5000 if running locally
#     port = int(os.environ.get("PORT", 5000))
    
#     # Bind to 0.0.0.0 so Render can route traffic to it
#     app.run(host="0.0.0.0", port=port)


# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# -------------------------------
# Main Flask application for AI Resume Screener
# -------------------------------
from nlp_extractor import extract_skills, _extract_text_from_pdf, _extract_text_from_docx
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import os
import pymongo
from pathlib import Path
from docx import Document
# Import your existing AI modules
from semantic_match import compute_similarity
from skill_gap import detect_skill_gaps
from llm import analyze_section
from fpdf import FPDF
import os
# -------------------------------
# Flask & MongoDB setup
# -------------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["ai_resume_screener"]

students = db["students"]
hr = db["hr"]
jd_collection = db['job_descriptions']
applications = db["applications"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# -------------------------------
# Landing Page
# -------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------------
# Student Authentication
# -------------------------------
@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].strip().lower()
        password = request.form['password']
        students.insert_one({'name': name, 'email': email, 'password': password})
        return redirect(url_for('student_login'))
    return render_template('student_signup.html')


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = students.find_one({'email': email})
        if user and user['password'] == password:
            session['student_id'] = str(user['_id'])
            return redirect(url_for('student_dashboard'))
        return render_template('student_login.html', error="Invalid credentials")
    return render_template('student_login.html')

# -------------------------------
# HR Authentication
# -------------------------------
@app.route('/hr_signup', methods=['GET', 'POST'])
def hr_signup():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        result = hr.insert_one({'email': email, 'password': password})
        session['hr_id'] = str(result.inserted_id)
        return redirect(url_for('hr_dashboard'))
    return render_template('hr_signup.html')


@app.route('/hr_login', methods=['GET', 'POST'])
def hr_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = hr.find_one({'email': email})
        if user and user['password'] == password:
            session['hr_id'] = str(user['_id'])
            return redirect(url_for('hr_dashboard'))
        return render_template('hr_login.html', error="Invalid credentials")
    return render_template('hr_login.html')

# -------------------------------
# Student Dashboard
# -------------------------------
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    apps = list(applications.find({'student_id': student_id}))
    return render_template('student_dashboard.html', applications=apps)

# -------------------------------
# Resume Upload & AI Processing
# -------------------------------
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    file = request.files['resume']
    filename = secure_filename(file.filename)
    resume_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(resume_path)

    # ✅ Detect file type and extract text
    if filename.lower().endswith(".pdf"):
        resume_text = _extract_text_from_pdf(Path(resume_path))
    elif filename.lower().endswith(".docx"):
        resume_text = _extract_text_from_docx(resume_path)
    else:
        return "Unsupported file format", 400

    # ✅ Load JD text from DB (fallback if empty)
    jd_doc = jd_collection.find_one() or {}
    jd_text = jd_doc.get("jd_text", "Generic job description text")

    # Run AI modules
    skills_result = extract_skills(resume_text, jd_text)
    resume_skills = skills_result["resume_skills"]
    jd_skills = skills_result["jd_skills"]

    similarity_score = compute_similarity(resume_text, jd_text)
    gap_report = detect_skill_gaps(resume_text, jd_text)
    section_feedback = analyze_section(resume_skills, jd_text)

    # Save report
    report_filename = f"report_{filename}.txt"
    report_path = os.path.join(REPORT_FOLDER, report_filename)
    matched_skills = [skill for skill in resume_skills if skill in jd_skills]
    missing_skills = [skill for skill in jd_skills if skill not in resume_skills]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("AI Resume Report\n")
        f.write(f"Score: {section_feedback.avg_score}\n")
        f.write(f"Matched Skills: {jd_skills}\n")
        f.write(f"Missing Skills: {[g.skill for g in gap_report.hard_gaps]}\n")
        for fb in section_feedback.bullets:
            f.write(f"- {fb.bullet} | Score {fb.score} | Suggestion: {fb.suggestion}\n")

    applications.insert_one({
        'student_id': session['student_id'],
        'resume_filename': filename,
        'report_filename': report_filename,
        'status': 'Pending',
        'created_at': datetime.now()
    })

    flash("✅ Resume submitted successfully!")
    return redirect(url_for('student_dashboard'))

# -------------------------------
# HR Dashboard
# -------------------------------
@app.route('/hr_dashboard')
def hr_dashboard():
    if 'hr_id' not in session:
        return redirect(url_for('hr_login'))

    apps = list(applications.find())
    for app in apps:
        student = students.find_one({'_id': ObjectId(app['student_id'])})
        app['student_name'] = student['name'] if student else 'Unknown'

    jd_doc = jd_collection.find_one() or {}
    current_jd = jd_doc.get("jd_text", "")

    return render_template('hr_dashboard.html', applications=apps, current_jd=current_jd)

# -------------------------------
# JD Update
# -------------------------------
@app.route('/set_jd', methods=['POST'])
def set_jd():
    if 'hr_id' not in session:
        return redirect(url_for('hr_login'))

    jd_text = request.form['jd_text']
    jd_collection.update_one({}, {"$set": {"jd_text": jd_text}}, upsert=True)

    flash("✅ Job Description updated successfully!")
    return redirect(url_for('hr_dashboard'))

# -------------------------------
# Application Detail Page
# -------------------------------
@app.route('/application/<id>')
def application_detail(id):
    app_data = applications.find_one({'_id': ObjectId(id)})
    if not app_data:
        return "Application not found", 404
    return render_template('application.html', app=app_data)

# -------------------------------
# Serve Files
# -------------------------------
@app.route('/view_resume/<filename>')
def view_resume(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/view_report/<filename>')
def view_report(filename):
    txt_path = os.path.join(REPORT_FOLDER, filename)
    if not os.path.exists(txt_path):
        return "Report not found", 404

    # ✅ Read the text report
    with open(txt_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    # ✅ Create a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in report_text.splitlines():
        pdf.multi_cell(0, 10, line)

    # ✅ Save temporary PDF
    pdf_filename = filename.replace(".txt", ".pdf")
    pdf_path = os.path.join(REPORT_FOLDER, pdf_filename)
    pdf.output(pdf_path)

    # ✅ Send PDF for download
    return send_file(pdf_path, as_attachment=True)
    
@app.route('/set_jd_page')
def set_jd_page():
    if 'hr_id' not in session:
        return redirect(url_for('hr_login'))
    return render_template('set_jd.html')

@app.route('/save_jd', methods=['POST'])
def save_jd():
    if 'hr_id' not in session:
        return redirect(url_for('hr_login'))

    jd_data = {
        "skills": request.form['skills'],
        "technologies": request.form['technologies'],
        "experience": request.form['experience'],
        "soft_skills": request.form['soft_skills']
    }

    jd_collection.update_one({}, {"$set": jd_data}, upsert=True)
    flash("✅ Job Description saved successfully!")
    return redirect(url_for('hr_dashboard'))

# -------------------------------
# Logout
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------------------
# Run app
# -------------------------------
if __name__ == "__main__":
    # Read the port dynamically from Render, default to 5000 if running locally
    port = int(os.environ.get("PORT", 5000))
    
    # Bind to 0.0.0.0 so Render can route traffic to it
    app.run(host="0.0.0.0", port=port)