from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
# import pandas as pd
import os
# import sys
import subprocess
import psutil
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, faculty, student
    email = db.Column(db.String(120), unique=True)
    
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    enrollment_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15))
    institute_email = db.Column(db.String(120), unique=True)
    course = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    department = db.Column(db.String(50))
    address = db.Column(db.Text)
    marks = db.relationship('Marks', backref='student', lazy=True)

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    exam_type = db.Column(db.String(50))  # Internal, External, etc.
    remarks = db.Column(db.Text)  # New field for remarks
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Add new model for profile edit requests
class ProfileEditRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)  # 'student' or 'faculty'
    requested_changes = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    response_date = db.Column(db.DateTime)
    response_message = db.Column(db.Text)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Redirect to appropriate dashboard based on role
    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session['role'] == 'faculty':
        return redirect(url_for('faculty_dashboard'))
    elif session['role'] == 'student':
        return redirect(url_for('student_dashboard'))
        
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['role'] = user.role
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
                
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    return render_template('faculty/dashboard.html')

@app.route('/faculty/take_attendance')
def take_attendance():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(current_dir, 'Main.py')
        
        # Start the attendance script
        process = subprocess.Popen(['python', main_script])
        session['attendance_pid'] = process.pid
        
        flash('Attendance system started successfully!')
    except Exception as e:
        flash(f'Error starting attendance: {str(e)}')
    
    return redirect(url_for('faculty_dashboard'))

@app.route('/faculty/view_attendance')
def view_attendance():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    attendance_data = []
    try:
        csv_path = 'Attendence.csv'
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as file:
                lines = file.readlines()
                
            data_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            
            for line in data_lines:
                parts = line.split(',')
                if len(parts) >= 4:  # Make sure we have all parts including period
                    attendance_data.append({
                        'Name': parts[0].strip(),
                        'Time': parts[1].strip(),
                        'Date': parts[2].strip(),
                        'Period': parts[3].strip() if len(parts) > 3 else 'N/A'
                    })
                    
            if not attendance_data:
                flash('No attendance records in the file!')
        else:
            flash('Attendence.csv file not found!')
    except Exception as e:
        flash(f'Error reading attendance: {str(e)}')
    
    return render_template('faculty/view_attendance.html', attendance_data=attendance_data)

@app.route('/faculty/end_attendance')
def end_attendance():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    try:
        pid = session.get('attendance_pid')
        if pid:
            if psutil.pid_exists(pid):
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                session.pop('attendance_pid', None)
                flash('Attendance system stopped successfully!')
            else:
                flash('Attendance process is not running!')
                session.pop('attendance_pid', None)
        else:
            flash('No attendance system running!')
    except Exception as e:
        flash(f'Error stopping attendance: {str(e)}')
    
    return redirect(url_for('faculty_dashboard'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/admin/manage_users')
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Get all students with their user information
    students = db.session.query(Student, User).join(User).all()
    
    # Get all faculty users
    faculty = User.query.filter_by(role='faculty').all()
    
    return render_template('admin/manage_users.html', students=students, faculty=faculty)

@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        user = User(username=username, password=password, role=role, email=email)
        db.session.add(user)
        db.session.commit()  # Ensure User ID is created before Student entry
        
        if role == 'student':
            student = Student(
                user_id=user.id,
                roll_no=request.form.get('roll_no'),
                name=request.form.get('name'),
                course=request.form.get('course'),
                semester=int(request.form.get('semester'))
            )
            db.session.add(student)
            db.session.commit()

        flash('User added successfully!')
        return redirect(url_for('manage_users'))
        
    return render_template('admin/add_user.html')

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'student':
        student = Student.query.filter_by(user_id=user_id).first()
        if student:
            db.session.delete(student)
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('manage_users'))

# Student routes
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student = Student.query.filter_by(user_id=session['user_id']).first()
    return render_template('student/dashboard.html', student=student)

@app.route('/student/profile')
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student = Student.query.filter_by(user_id=session['user_id']).first()
    return render_template('student/profile.html', student=student)

@app.route('/student/edit_profile_request', methods=['GET', 'POST'])
def student_edit_profile_request():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        changes = {
            'name': request.form.get('name'),
            'phone_number': request.form.get('phone_number'),
            'address': request.form.get('address'),
            'semester': request.form.get('semester'),
            'department': request.form.get('department')
        }
        
        edit_request = ProfileEditRequest(
            user_id=session['user_id'],
            request_type='student',
            requested_changes=str(changes)
        )
        db.session.add(edit_request)
        db.session.commit()
        flash('Profile edit request submitted successfully!')
        return redirect(url_for('student_profile'))
    
    student = Student.query.filter_by(user_id=session['user_id']).first()
    return render_template('student/edit_profile_request.html', student=student)

@app.route('/student/marks')
def view_marks():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student = Student.query.filter_by(user_id=session['user_id']).first()
    marks = Marks.query.filter_by(student_id=student.id).all()
    return render_template('student/marks.html', marks=marks)

@app.route('/student/notices')
def view_notices():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    return render_template('student/notices.html', notices=notices)

# Faculty additional route for posting notices
@app.route('/faculty/post_notice', methods=['GET', 'POST'])
def post_notice():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        notice = Notice(
            title=request.form.get('title'),
            content=request.form.get('content'),
            posted_by=session['user_id']
        )
        db.session.add(notice)
        db.session.commit()
        flash('Notice posted successfully!')
        return redirect(url_for('faculty_dashboard'))
        
    return render_template('faculty/post_notice.html')

# Add these routes for faculty to manage marks and notices
@app.route('/faculty/add_marks', methods=['GET', 'POST'])
def add_marks():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        student_roll = request.form.get('roll_no')
        subject = request.form.get('subject')
        marks_obtained = float(request.form.get('marks'))
        max_marks = float(request.form.get('max_marks'))
        exam_type = request.form.get('exam_type')
        remarks = request.form.get('remarks')
        
        student = Student.query.filter_by(roll_no=student_roll).first()
        if student:
            mark = Marks(
                student_id=student.id,
                subject=subject,
                marks=marks_obtained,
                max_marks=max_marks,
                exam_type=exam_type,
                remarks=remarks
            )
            db.session.add(mark)
            db.session.commit()
            flash('Marks added successfully!')
        else:
            flash('Student not found!')
            
    students = Student.query.all()
    return render_template('faculty/add_marks.html', students=students)

# Faculty profile edit request route
@app.route('/faculty/edit_profile_request', methods=['GET', 'POST'])
def faculty_edit_profile_request():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        changes = {
            'name': request.form.get('name'),
            'phone_number': request.form.get('phone_number'),
            'email': request.form.get('email'),
            'department': request.form.get('department')
        }
        
        edit_request = ProfileEditRequest(
            user_id=session['user_id'],
            request_type='faculty',
            requested_changes=str(changes)
        )
        db.session.add(edit_request)
        db.session.commit()
        flash('Profile edit request submitted successfully!')
        return redirect(url_for('faculty_dashboard'))
    
    faculty = User.query.get(session['user_id'])
    return render_template('faculty/edit_profile_request.html', faculty=faculty)

# Admin routes for managing edit requests
@app.route('/admin/edit_requests')
def admin_edit_requests():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    pending_requests = ProfileEditRequest.query.filter_by(status='pending').all()
    return render_template('admin/edit_requests.html', requests=pending_requests)

@app.route('/admin/handle_edit_request/<int:request_id>/<action>')
def handle_edit_request(request_id, action):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    edit_request = ProfileEditRequest.query.get_or_404(request_id)
    edit_request.status = action
    edit_request.response_date = datetime.utcnow()
    
    if action == 'approved':
        changes = eval(edit_request.requested_changes)
        if edit_request.request_type == 'student':
            student = Student.query.filter_by(user_id=edit_request.user_id).first()
            for key, value in changes.items():
                if value and hasattr(student, key):
                    setattr(student, key, value)
        else:  # faculty
            faculty = User.query.get(edit_request.user_id)
            for key, value in changes.items():
                if value and hasattr(faculty, key):
                    setattr(faculty, key, value)
    
    db.session.commit()
    flash(f'Edit request {action}!')
    return redirect(url_for('admin_edit_requests'))

# Add sample student data route
@app.route('/admin/add_sample_students')
def add_sample_students():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    sample_students = [
        {
            'username': 'student1',
            'password': 'pass123',
            'email': 'student1@institute.edu',
            'enrollment_number': 'EN2024001',
            'name': 'John Doe',
            'phone_number': '1234567890',
            'course': 'B.Tech',
            'semester': 4,
            'department': 'Computer Engineering'
        },
        {
            'username': 'student2',
            'password': 'pass123',
            'email': 'student2@institute.edu',
            'enrollment_number': 'EN2024002',
            'name': 'Jane Smith',
            'phone_number': '9876543210',
            'course': 'B.Tech',
            'semester': 4,
            'department': 'Computer Engineering'
        }
    ]
    
    for student_data in sample_students:
        user = User(
            username=student_data['username'],
            password=student_data['password'],
            role='student',
            email=student_data['email']
        )
        db.session.add(user)
        db.session.commit()
        
        student = Student(
            user_id=user.id,
            enrollment_number=student_data['enrollment_number'],
            name=student_data['name'],
            phone_number=student_data['phone_number'],
            institute_email=student_data['email'],
            course=student_data['course'],
            semester=student_data['semester'],
            department=student_data['department']
        )
        db.session.add(student)
    
    db.session.commit()
    flash('Sample student data added successfully!')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
