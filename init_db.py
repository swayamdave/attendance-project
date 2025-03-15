from app import app, db, User, Student, Marks, Notice
from datetime import datetime

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Create admin user
    admin = User(
        username='admin',
        password='admin123',
        role='admin',
        email='admin@example.com'
    )
    db.session.add(admin)
    
    # Create faculty user
    faculty = User(
        username='faculty',
        password='password',
        role='faculty',
        email='faculty@example.com'
    )
    db.session.add(faculty)
    
    # Create sample student user
    student = User(
        username='student',
        password='student123',
        role='student',
        email='student@example.com'
    )
    db.session.add(student)
    db.session.commit()
    
    # Add student details
    student_details = Student(
        user_id=student.id,
        roll_no='2023001',
        name='John Doe',
        course='B.Tech',
        semester=3
    )
    db.session.add(student_details)
    
    # Add sample marks (optional)
    sample_mark = Marks(
        student_id=1,
        subject='Sample Subject',
        marks=85.0,
        max_marks=100.0,
        exam_type='Internal',
        remarks='Sample remarks',
        date_added=datetime.now()
    )
    db.session.add(sample_mark)
    
    # Add sample notice (optional)
    sample_notice = Notice(
        title='Welcome Notice',
        content='Welcome to the new semester!',
        date_posted=datetime.now(),
        posted_by=2  # faculty id
    )
    db.session.add(sample_notice)
    
    db.session.commit()
    print("Database initialized successfully with all tables and sample data!")