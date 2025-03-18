from app import app, db, User, Student, Marks, Notice, ProfileEditRequest
from datetime import datetime

def init_db():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password='admin123',  # In production, use proper password hashing
                role='admin',
                email='admin@institute.edu'
            )
            db.session.add(admin)
            db.session.commit()

        # Add sample faculty
        faculty = User.query.filter_by(username='faculty1').first()
        if not faculty:
            faculty = User(
                username='faculty1',
                password='faculty123',
                role='faculty',
                email='faculty1@institute.edu'
            )
            db.session.add(faculty)
            db.session.commit()

        # Add sample students
        sample_students = [
            {
                'username': 'student1',
                'password': 'student123',
                'email': 'student1@institute.edu',
                'enrollment_number': 'EN2024001',
                'name': 'John Doe',
                'phone_number': '1234567890',
                'course': 'B.Tech',
                'semester': 4,
                'department': 'Computer Engineering',
                'institute_email': 'john.doe@institute.edu',
                'address': '123 Student Housing, Campus'
            },
            {
                'username': 'student2',
                'password': 'student123',
                'email': 'student2@institute.edu',
                'enrollment_number': 'EN2024002',
                'name': 'Jane Smith',
                'phone_number': '9876543210',
                'course': 'B.Tech',
                'semester': 4,
                'department': 'Computer Engineering',
                'institute_email': 'jane.smith@institute.edu',
                'address': '456 Student Housing, Campus'
            }
        ]

        for student_data in sample_students:
            student = Student.query.filter_by(enrollment_number=student_data['enrollment_number']).first()
            if not student:
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
                    institute_email=student_data['institute_email'],
                    course=student_data['course'],
                    semester=student_data['semester'],
                    department=student_data['department'],
                    address=student_data['address']
                )
                db.session.add(student)
                db.session.commit()

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

if __name__ == '__main__':
    init_db()