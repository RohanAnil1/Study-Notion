import json
import os
from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    profile_pic = db.Column(db.String(256), default='uploads/profile_pics/default_instructor.svg')
    role = db.Column(db.String(20), default='student')  # 'student' or 'instructor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    enrollments = db.relationship('Enrollment', backref='user', lazy='dynamic')
    created_courses = db.relationship('Course', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_instructor(self):
        return self.role == 'instructor'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    courses = db.relationship('Course', backref='category', lazy='dynamic')


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    instructor = db.Column(db.String(128))
    thumbnail = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_published = db.Column(db.Boolean, default=False)
    
    sections = db.relationship('Section', backref='course', lazy='dynamic', order_by='Section.order')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')
    
    def get_progress(self, user_id):
        from models import Enrollment, Lecture, LectureProgress
        enrollment = Enrollment.query.filter_by(user_id=user_id, course_id=self.id).first()
        if not enrollment:
            return 0
            
        total_lectures = Lecture.query.join(Section).filter(Section.course_id == self.id).count()
        if total_lectures == 0:
            return 0
            
        completed_lectures = LectureProgress.query.join(Lecture).join(Section).filter(
            Section.course_id == self.id,
            LectureProgress.user_id == user_id,
            LectureProgress.completed == True
        ).count()
        
        return int((completed_lectures / total_lectures) * 100)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='module', lazy='dynamic', order_by='Lesson.order')
    quizzes = db.relationship('Quiz', backref='module', lazy='dynamic')


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    
    lectures = db.relationship('Lecture', backref='section', lazy='dynamic', order_by='Lecture.order')


class Lecture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(256))
    video_type = db.Column(db.String(20))  # 'youtube', 'vimeo', 'upload', etc.
    video_id = db.Column(db.String(50))    # ID for embedded videos (YouTube, etc.)
    content = db.Column(db.Text)           # HTML content
    duration = db.Column(db.Integer)       # Duration in seconds
    order = db.Column(db.Integer)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    progress = db.relationship('LectureProgress', backref='lecture', lazy='dynamic')
    quizzes = db.relationship('Quiz', backref='lecture', lazy='dynamic')


class LectureProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'))
    current_position = db.Column(db.Integer, default=0)  # Position in seconds
    completed = db.Column(db.Boolean, default=False)
    last_watched = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('lecture_progress', lazy='dynamic'))


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic')
    creator = db.relationship('User', backref=db.backref('created_quizzes', lazy='dynamic'))


class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    
    options = db.relationship('QuizOption', backref='question', lazy='dynamic')


class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'))


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('quiz_attempts', lazy='dynamic'))
    quiz = db.relationship('Quiz', backref=db.backref('attempts', lazy='dynamic'))


class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    completed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('progress', lazy='dynamic'))
    module = db.relationship('Module', backref=db.backref('user_progress', lazy='dynamic'))
    lesson = db.relationship('Lesson', backref=db.backref('user_progress', lazy='dynamic'))


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # 'image', 'video', 'document'
    file_size = db.Column(db.Integer)     # Size in bytes
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('media', lazy='dynamic'))


def load_initial_data():
    """Load initial data from JSON files if tables are empty"""
    # Only load data if no categories exist yet
    if Category.query.count() == 0:
        try:
            # Define the path to the courses data file
            data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'courses.json')
            
            # Check if the file exists
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Create categories
                categories_map = {}
                for category_data in data.get('categories', []):
                    category = Category(
                        name=category_data['name'],
                        description=category_data.get('description', '')
                    )
                    db.session.add(category)
                    db.session.flush()  # To get the ID
                    categories_map[category_data['name']] = category.id
                
                # Create courses
                for course_data in data.get('courses', []):
                    category_id = categories_map.get(course_data.get('category'), None)
                    course = Course(
                        title=course_data['title'],
                        description=course_data.get('description', ''),
                        instructor=course_data.get('instructor', 'Unknown'),
                        thumbnail=course_data.get('thumbnail', ''),
                        category_id=category_id,
                        is_published=True
                    )
                    db.session.add(course)
                    db.session.flush()  # To get the ID
                    
                    # Create sections and lectures
                    for section_idx, section_data in enumerate(course_data.get('sections', []), 1):
                        section = Section(
                            title=section_data['title'],
                            description=section_data.get('description', ''),
                            order=section_idx,
                            course_id=course.id
                        )
                        db.session.add(section)
                        db.session.flush()
                        
                        for lecture_idx, lecture_data in enumerate(section_data.get('lectures', []), 1):
                            # Parse YouTube URL if it exists
                            video_type = None
                            video_id = None
                            video_url = lecture_data.get('video_url', '')
                            
                            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                                video_type = 'youtube'
                                # Extract YouTube ID
                                if 'v=' in video_url:
                                    video_id = video_url.split('v=')[1].split('&')[0]
                                elif 'youtu.be/' in video_url:
                                    video_id = video_url.split('youtu.be/')[1].split('?')[0]
                            
                            lecture = Lecture(
                                title=lecture_data['title'],
                                description=lecture_data.get('description', ''),
                                video_url=video_url,
                                video_type=video_type,
                                video_id=video_id,
                                content=lecture_data.get('content', ''),
                                duration=lecture_data.get('duration', 0),
                                order=lecture_idx,
                                section_id=section.id
                            )
                            db.session.add(lecture)
                
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error loading initial data: {e}")
