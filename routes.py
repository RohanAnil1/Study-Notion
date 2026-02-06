from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import (
    User, Course, Section, Lecture, Category, Enrollment, LectureProgress, 
    Quiz, QuizQuestion, QuizOption, QuizAttempt, Media, Module, Lesson, UserProgress
)
from forms import (
    LoginForm, RegistrationForm, CourseForm, SectionForm, LectureForm,
    ProfileForm, SearchForm, MediaUploadForm, QuizGeneratorForm, ModuleForm, LessonForm, QuizForm, QuizQuestionForm
)
from ai_services import generate_quiz_from_content, summarize_content, generate_study_notes, generate_course_content
from utils import allowed_file, extract_youtube_id, save_uploaded_file, delete_uploaded_file, fetch_playlist_data
import logging
import os
import json
from datetime import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

# Instructor required decorator
def instructor_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'instructor':
            flash('Access denied. You need instructor privileges to access this page.', 'danger')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Update all route decorators to use the blueprint
@main_bp.route('/')
def index():
    try:
        featured_courses = Course.query.filter_by(is_published=True).limit(6).all()
        categories = Category.query.all()
        return render_template('index.html', 
                           featured_courses=featured_courses, 
                           categories=categories)
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        flash('An error occurred while loading the courses.', 'error')
        return render_template('index.html', courses=[])


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html', form=form)
            
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data  # Set the role from the form
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user: {e}")
            flash('An error occurred during registration', 'danger')
            
    return render_template('register.html', form=form)


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return render_template('login.html', form=form)
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        if not next_page or not next_page.startswith('/'):
            # Redirect instructors to instructor dashboard, students to normal home
            if user.role == 'instructor':
                next_page = url_for('main.instructor_dashboard')
            else:
                next_page = url_for('main.index')
            
        flash('Login successful!', 'success')
        return redirect(next_page)
        
    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        
        # Handle profile picture upload
        if form.profile_pic.data:
            success, message, profile_pic_path = save_uploaded_file(
                form.profile_pic.data,
                folder_type='profile_pic',
                file_type='image'
            )
            if success:
                current_user.profile_pic = profile_pic_path
            else:
                flash(message, 'error')
                return render_template('profile.html', form=form, user=current_user)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile.', 'error')
    
    # Get enrollment data
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    courses = []
    
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            progress = course.get_progress(current_user.id)
            courses.append({
                'course': course,
                'progress': progress,
                'last_accessed': enrollment.last_accessed
            })
    
    return render_template('profile.html', 
                           user=current_user, 
                           enrolled_courses=courses, 
                           form=form)


@main_bp.route('/courses')
def course_catalog():
    search_form = SearchForm()
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '')
    
    # Base query - only show published courses to regular users
    query = Course.query.filter_by(is_published=True)
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    if search_query:
        query = query.filter(Course.title.ilike(f'%{search_query}%'))
    
    # Get all courses that match the criteria
    courses = query.all()
    categories = Category.query.all()
    
    return render_template('course_catalog.html', 
                          courses=courses, 
                          categories=categories,
                          selected_category=category_id,
                          search_query=search_query,
                          form=search_form)


@main_bp.route('/course/<int:course_id>')
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Only allow viewing published courses unless you're the instructor
    if not course.is_published and (not current_user.is_authenticated or current_user.id != course.creator_id):
        flash('This course is not currently available.', 'warning')
        return redirect(url_for('main.course_catalog'))
        
    is_enrolled = False
    progress = 0
    
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        is_enrolled = enrollment is not None
        if is_enrolled:
            progress = course.get_progress(current_user.id)
    
    return render_template('course_details.html', 
                          course=course, 
                          is_enrolled=is_enrolled,
                          progress=progress,
                          Section=Section,
                          Lecture=Lecture,
                          Course=Course)


@main_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Only allow enrolling in published courses
    if not course.is_published:
        flash('This course is not currently available for enrollment.', 'warning')
        return redirect(url_for('main.course_catalog'))
    
    # Check if already enrolled
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if enrollment:
        flash('You are already enrolled in this course', 'info')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    # Create new enrollment
    new_enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
    
    try:
        db.session.add(new_enrollment)
        db.session.commit()
        flash('Successfully enrolled in the course!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error enrolling in course: {e}")
        flash('An error occurred during enrollment', 'danger')
    
    return redirect(url_for('main.course_details', course_id=course.id))


@main_bp.route('/lecture/<int:lecture_id>')
@login_required
def video_player(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Check if user is enrolled or is the course creator
    is_enrolled = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
    is_creator = current_user.id == course.creator_id
    
    if not (is_enrolled or is_creator):
        flash('You must enroll in the course to access this lecture', 'warning')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    # Update last accessed time if student
    if is_enrolled:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        enrollment.last_accessed = db.func.now()
    
    # Get or create lecture progress
    progress = LectureProgress.query.filter_by(user_id=current_user.id, lecture_id=lecture.id).first()
    if not progress:
        progress = LectureProgress(user_id=current_user.id, lecture_id=lecture.id)
        db.session.add(progress)
    
    # Get all lectures in the course for navigation
    course_sections = Section.query.filter_by(course_id=course.id).order_by(Section.order).all()
    
    # Get related quizzes
    quizzes = Quiz.query.filter_by(lecture_id=lecture.id).all()
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating lecture progress: {e}")
    
    # Get next and previous lectures for navigation
    next_lecture = None
    prev_lecture = None
    
    # Logic to find next lecture
    if lecture.order < Lecture.query.filter_by(section_id=section.id).count():
        next_lecture = Lecture.query.filter_by(section_id=section.id, order=lecture.order+1).first()
    else:
        # Check if there's a next section
        next_section = Section.query.filter_by(course_id=course.id, order=section.order+1).first()
        if next_section:
            next_lecture = Lecture.query.filter_by(section_id=next_section.id, order=1).first()
    
    # Logic to find previous lecture
    if lecture.order > 1:
        prev_lecture = Lecture.query.filter_by(section_id=section.id, order=lecture.order-1).first()
    else:
        # Check if there's a previous section
        prev_section = Section.query.filter_by(course_id=course.id, order=section.order-1).first()
        if prev_section:
            last_lecture_in_prev = Lecture.query.filter_by(section_id=prev_section.id).order_by(Lecture.order.desc()).first()
            if last_lecture_in_prev:
                prev_lecture = last_lecture_in_prev
    
    return render_template('video_player.html', 
                          lecture=lecture,
                          section=section,
                          course=course,
                          progress=progress,
                          course_sections=course_sections,
                          current_position=progress.current_position if progress else 0,
                          quizzes=quizzes,
                          next_lecture=next_lecture,
                          prev_lecture=prev_lecture,
                          is_creator=is_creator,
                          Lecture=Lecture)


@main_bp.route('/update-progress', methods=['POST'])
@login_required
def update_progress():
    lecture_id = request.form.get('lecture_id', type=int)
    current_position = request.form.get('current_position', type=int)
    completed = request.form.get('completed', type=bool)
    
    if not lecture_id:
        return jsonify({'status': 'error', 'message': 'Lecture ID is required'}), 400
    
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Get or create lecture progress
    progress = LectureProgress.query.filter_by(user_id=current_user.id, lecture_id=lecture.id).first()
    if not progress:
        progress = LectureProgress(user_id=current_user.id, lecture_id=lecture.id)
        db.session.add(progress)
    
    # Update progress
    progress.current_position = current_position
    if completed is not None:
        progress.completed = completed
    
    try:
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating progress: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/generate-quiz/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
def generate_quiz_page(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Check if the user is enrolled or is the creator
    is_enrolled = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
    is_creator = current_user.id == course.creator_id
    
    current_app.logger.info(f"Quiz generation request - User: {current_user.id}, Lecture: {lecture_id}, Is Creator: {is_creator}, Is Enrolled: {is_enrolled}")
    
    if not (is_enrolled or is_creator):
        flash('You must be enrolled in the course to access quizzes', 'warning')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    # Get existing quiz
    quiz = Quiz.query.filter_by(lecture_id=lecture.id).first()
    current_app.logger.info(f"Existing quiz found: {quiz is not None}")
    
    # If POST request, check if we should create a new quiz
    form = QuizGeneratorForm()
    if request.method == 'POST' and form.validate_on_submit():
        current_app.logger.info("POST request received for quiz generation")
        # If generating a new quiz and one already exists
        if quiz and form.generate_new.data:
            current_app.logger.info("Deleting existing quiz for regeneration")
            db.session.delete(quiz)
            db.session.commit()
            quiz = None
            
        # If custom number of questions
        num_questions = form.num_questions.data
        current_app.logger.info(f"Number of questions requested: {num_questions}")
            
        # Generate the quiz if needed
        if not quiz:
            try:
                # Get lecture content for quiz generation
                content = lecture.content
                current_app.logger.info(f"Lecture content length: {len(content) if content else 0}")
                
                if not content or len(content) < 50:
                    flash('Not enough content to generate a quiz', 'warning')
                    return redirect(url_for('main.video_player', lecture_id=lecture.id))
                
                # Generate a quiz based on the lecture content (using the ai_services function)
                current_app.logger.info("Starting quiz generation with AI service")
                quiz_data = generate_quiz_from_content(content, num_questions)
                
                if 'error' in quiz_data:
                    current_app.logger.error(f"Error in quiz data: {quiz_data['error']}")
                    flash(f"Error generating quiz: {quiz_data['error']}", 'danger')
                    return redirect(url_for('main.video_player', lecture_id=lecture.id))
                
                current_app.logger.info("Quiz data generated successfully, creating database entries")
                # Create new quiz
                new_quiz = Quiz(
                    title=f"Quiz for {lecture.title}",
                    description=f"Test your knowledge on {lecture.title}",
                    lecture_id=lecture.id,
                    created_by=current_user.id
                )
                db.session.add(new_quiz)
                db.session.flush()
                
                # Add questions and options
                for q_data in quiz_data['questions']:
                    question = QuizQuestion(
                        question=q_data['question'],
                        quiz_id=new_quiz.id
                    )
                    db.session.add(question)
                    db.session.flush()
                    
                    for opt_data in q_data['options']:
                        option = QuizOption(
                            option_text=opt_data['text'],
                            is_correct=opt_data['is_correct'],
                            question_id=question.id
                        )
                        db.session.add(option)
                
                db.session.commit()
                quiz = new_quiz
                current_app.logger.info("Quiz created and saved successfully")
                flash('Quiz generated successfully!', 'success')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error generating quiz: {str(e)}")
                current_app.logger.error(f"Error type: {type(e).__name__}")
                import traceback
                current_app.logger.error(f"Traceback:\n{traceback.format_exc()}")
                flash('Failed to generate quiz. Please try again later.', 'danger')
                return redirect(url_for('main.video_player', lecture_id=lecture.id))
    
    # Fetch questions and options for the quiz
    questions = []
    if quiz:
        for question in QuizQuestion.query.filter_by(quiz_id=quiz.id).all():
            options = QuizOption.query.filter_by(question_id=question.id).all()
            questions.append({
                'question': question,
                'options': options
            })
    
    return render_template('quiz.html', 
                         quiz=quiz, 
                         lecture=lecture,
                         questions=questions,
                         form=form,
                         is_creator=is_creator,
                         Lecture=Lecture,
                         Section=Section,
                         Course=Course)


@main_bp.route('/submit-quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    lecture = Lecture.query.get(quiz.lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Check if the user is enrolled
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enrollment:
        flash('You must be enrolled in the course to submit quizzes', 'warning')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    # Get all questions for this quiz
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
    
    score = 0
    total_questions = len(questions)
    
    # Check each answer
    for question in questions:
        selected_option_id = request.form.get(f'question_{question.id}')
        if selected_option_id:
            option = QuizOption.query.get(int(selected_option_id))
            if option and option.is_correct:
                score += 1
    
    percentage = (score / total_questions * 100) if total_questions > 0 else 0
    
    # Create quiz attempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score,
        total_questions=total_questions
    )
    
    try:
        db.session.add(attempt)
        db.session.commit()
        
        # Auto-mark lecture as completed if quiz score is good
        if percentage >= 70:
            progress = LectureProgress.query.filter_by(user_id=current_user.id, lecture_id=lecture.id).first()
            if progress:
                progress.completed = True
                db.session.commit()
        
        flash(f'Quiz submitted! You scored {score} out of {total_questions} ({percentage:.1f}%)', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting quiz: {e}")
        flash('An error occurred while submitting the quiz.', 'danger')
    
    return redirect(url_for('main.video_player', lecture_id=lecture.id))


@main_bp.route('/generate-study-notes/<int:lecture_id>')
@login_required
def generate_study_notes_route(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Check if user is enrolled or is creator
    is_enrolled = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
    is_creator = current_user.id == course.creator_id
    
    if not (is_enrolled or is_creator):
        flash('You must be enrolled in the course to access this feature', 'warning')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    try:
        content = lecture.content
        if not content or len(content) < 50:
            flash('Not enough content to generate study notes', 'warning')
            return redirect(url_for('main.video_player', lecture_id=lecture.id))
        
        # Generate study notes based on the lecture content (using the ai_services function)
        study_notes = generate_study_notes(content)
        
        return render_template('study_notes.html',
                              lecture=lecture,
                              course=course,
                              study_notes=study_notes,
                              Lecture=Lecture,
                              Section=Section,
                              Course=Course)
    except Exception as e:
        current_app.logger.error(f"Error generating study notes: {e}")
        flash('Failed to generate study notes. Please try again later.', 'danger')
        return redirect(url_for('main.video_player', lecture_id=lecture.id))


@main_bp.route('/summarize-lecture/<int:lecture_id>')
@login_required
def summarize_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Check if user is enrolled or is creator
    is_enrolled = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
    is_creator = current_user.id == course.creator_id
    
    if not (is_enrolled or is_creator):
        flash('You must be enrolled in the course to access this feature', 'warning')
        return redirect(url_for('main.course_details', course_id=course.id))
    
    try:
        content = lecture.content
        if not content or len(content) < 50:
            flash('Not enough content to generate a summary', 'warning')
            return redirect(url_for('main.video_player', lecture_id=lecture.id))
        
        # Generate a summary of the lecture content (using the ai_services function)
        summary = summarize_content(content)
        
        return render_template('lecture_summary.html',
                              lecture=lecture,
                              course=course,
                              summary=summary,
                              Lecture=Lecture,
                              Section=Section,
                              Course=Course)
    except Exception as e:
        current_app.logger.error(f"Error summarizing lecture: {e}")
        flash('Failed to generate summary. Please try again later.', 'danger')
        return redirect(url_for('main.video_player', lecture_id=lecture.id))


# Instructor routes
@main_bp.route('/instructor/dashboard')
@login_required
@instructor_required
def instructor_dashboard():
    # Get courses created by this instructor
    courses = Course.query.filter_by(creator_id=current_user.id).all()
    
    # Get stats for each course
    course_stats = []
    for course in courses:
        enrollments_count = Enrollment.query.filter_by(course_id=course.id).count()
        
        # Calculate average progress across all students
        total_progress = 0
        students = Enrollment.query.filter_by(course_id=course.id).all()
        for student in students:
            total_progress += course.get_progress(student.user_id)
        
        avg_progress = total_progress / enrollments_count if enrollments_count > 0 else 0
        
        # Get most recent enrollment
        latest_enrollment = Enrollment.query.filter_by(course_id=course.id).order_by(Enrollment.enrolled_at.desc()).first()
        
        course_stats.append({
            'course': course,
            'enrollments': enrollments_count,
            'avg_progress': avg_progress,
            'latest_enrollment': latest_enrollment
        })
    
    # Get recent media files
    recent_media = Media.query.filter_by(user_id=current_user.id).order_by(Media.uploaded_at.desc()).limit(5).all()
    
    return render_template('instructor/dashboard.html',
                        course_stats=course_stats,
                        recent_media=recent_media)


@main_bp.route('/instructor/courses')
@login_required
@instructor_required
def instructor_courses():
    courses = Course.query.filter_by(creator_id=current_user.id).all()
    return render_template('instructor/courses.html', courses=courses)


@main_bp.route('/instructor/course/new', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_course():
    form = CourseForm()
    # Get categories for the select field
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        try:
            # Handle thumbnail upload
            thumbnail_path = None
            if form.thumbnail.data:
                success, message, thumbnail_path = save_uploaded_file(
                    form.thumbnail.data,
                    folder_type='course_thumbnail',
                    file_type='image'
                )
                if not success:
                    flash(message, 'error')
                    return render_template('instructor/course_editor.html', form=form, is_new=True)
            
            # Create new course
            course = Course(
                title=form.title.data,
                description=form.description.data,
                category_id=form.category_id.data,
                creator_id=current_user.id,
                thumbnail=thumbnail_path,
                instructor=f"{current_user.first_name} {current_user.last_name}"
            )
            
            db.session.add(course)
            db.session.commit()
            
            flash('Course created successfully!', 'success')
            return redirect(url_for('main.instructor_courses'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating course: {str(e)}")
            flash('An error occurred while creating the course.', 'error')
    
    return render_template('instructor/course_editor.html', form=form, is_new=True)


@main_bp.route('/instructor/course/import-playlist', methods=['GET', 'POST'])
@login_required
@instructor_required
def import_playlist():
    categories = Category.query.all()
    category_choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'fetch':
            playlist_url = request.form.get('playlist_url', '').strip()
            if not playlist_url:
                flash('Please enter a YouTube playlist URL.', 'error')
                return render_template('instructor/import_playlist.html',
                                       categories=category_choices)

            flash('Fetching playlist data... This may take a moment for large playlists.', 'info')
            playlist_data, error = fetch_playlist_data(playlist_url)

            if error:
                flash(error, 'error')
                return render_template('instructor/import_playlist.html',
                                       categories=category_choices,
                                       playlist_url=playlist_url)

            if not playlist_data or not playlist_data.get('videos'):
                flash('No videos found in this playlist.', 'error')
                return render_template('instructor/import_playlist.html',
                                       categories=category_choices,
                                       playlist_url=playlist_url)

            return render_template('instructor/import_playlist.html',
                                   categories=category_choices,
                                   playlist_data=playlist_data,
                                   playlist_url=playlist_url,
                                   selected_category=request.form.get('category_id', ''))

        elif action == 'create':
            try:
                playlist_title = request.form.get('course_title', 'Untitled Course').strip()
                playlist_desc = request.form.get('course_description', '').strip()
                category_id = request.form.get('category_id')

                # Gather video data from the form
                video_indices = request.form.getlist('selected_videos')
                if not video_indices:
                    flash('Please select at least one video to import.', 'error')
                    return redirect(url_for('main.import_playlist'))

                # Create the course
                course = Course(
                    title=playlist_title,
                    description=playlist_desc,
                    category_id=int(category_id) if category_id else None,
                    creator_id=current_user.id,
                    instructor=f"{current_user.first_name} {current_user.last_name}",
                    is_published=False
                )
                db.session.add(course)
                db.session.flush()

                # Create a section + lecture for each selected video
                for order, idx in enumerate(video_indices, 1):
                    v_title = request.form.get(f'video_title_{idx}', f'Chapter {order}')
                    v_url = request.form.get(f'video_url_{idx}', '')
                    v_duration = request.form.get(f'video_duration_{idx}', '0')
                    v_description = request.form.get(f'video_description_{idx}', '')
                    v_id = request.form.get(f'video_id_{idx}', '')

                    section = Section(
                        title=v_title,
                        description=v_description[:300] if v_description else '',
                        order=order,
                        course_id=course.id
                    )
                    db.session.add(section)
                    db.session.flush()

                    lecture = Lecture(
                        title=v_title,
                        description=v_description,
                        video_url=v_url,
                        video_type='youtube',
                        video_id=v_id,
                        content=v_description if v_description else '',
                        duration=int(v_duration) if v_duration else 0,
                        order=1,
                        section_id=section.id
                    )
                    db.session.add(lecture)

                db.session.commit()
                flash(f'Course "{playlist_title}" created with {len(video_indices)} chapters!', 'success')
                return redirect(url_for('main.edit_course', course_id=course.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error importing playlist: {str(e)}")
                flash(f'Error creating course: {str(e)}', 'error')

    return render_template('instructor/import_playlist.html',
                           categories=category_choices)


@main_bp.route('/instructor/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.creator_id != current_user.id:
        flash('You do not have permission to edit this course.', 'error')
        return redirect(url_for('main.instructor_courses'))
    
    form = CourseForm(obj=course)
    # Get categories for the select field
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        try:
            # Handle thumbnail update
            if form.thumbnail.data:
                # Delete old thumbnail if it exists
                if course.thumbnail:
                    delete_uploaded_file(course.thumbnail)
                
                # Save new thumbnail
                success, message, thumbnail_path = save_uploaded_file(
                    form.thumbnail.data,
                    folder_type='course_thumbnail',
                    file_type='image'
                )
                if not success:
                    flash(message, 'error')
                    return render_template('instructor/course_editor.html', form=form, course=course)
                
                course.thumbnail = thumbnail_path
            
            # Update course details
            course.title = form.title.data
            course.description = form.description.data
            course.category_id = form.category_id.data
            course.instructor = f"{current_user.first_name} {current_user.last_name}"
            
            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('main.instructor_courses'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating course: {str(e)}")
            flash('An error occurred while updating the course.', 'error')
    
    # Get sections ordered by their order field
    sections = Section.query.filter_by(course_id=course.id).order_by(Section.order).all()
    
    return render_template('instructor/course_editor.html', 
                         form=form, 
                         course=course,
                         sections=sections,
                         is_new=False)


@main_bp.route('/instructor/course/<int:course_id>/publish', methods=['POST'])
@login_required
@instructor_required
def publish_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure instructor can only publish their own courses
    if course.creator_id != current_user.id:
        flash('You can only publish your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    # Toggle publish state
    course.is_published = not course.is_published
    
    try:
        db.session.commit()
        state = "published" if course.is_published else "unpublished"
        flash(f'Course {state} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling course publish state: {e}")
        flash('An error occurred while updating the course.', 'danger')
    
    return redirect(url_for('main.edit_course', course_id=course.id))


@main_bp.route('/instructor/course/<int:course_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure instructor can only delete their own courses
    if course.creator_id != current_user.id:
        flash('You can only delete your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    try:
        # Delete associated sections, lectures, and enrollments
        sections = Section.query.filter_by(course_id=course.id).all()
        for section in sections:
            lectures = Lecture.query.filter_by(section_id=section.id).all()
            for lecture in lectures:
                LectureProgress.query.filter_by(lecture_id=lecture.id).delete()
                quizzes = Quiz.query.filter_by(lecture_id=lecture.id).all()
                for quiz in quizzes:
                    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
                    for question in questions:
                        QuizOption.query.filter_by(question_id=question.id).delete()
                    QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
                    QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
                    db.session.delete(quiz)
                db.session.delete(lecture)
            db.session.delete(section)
        
        Enrollment.query.filter_by(course_id=course.id).delete()
        db.session.delete(course)
        db.session.commit()
        
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting course: {e}")
        flash('An error occurred while deleting the course.', 'danger')
    
    return redirect(url_for('main.instructor_courses'))


@main_bp.route('/instructor/course/<int:course_id>/section/new', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_section(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure instructor can only add sections to their own courses
    if course.creator_id != current_user.id:
        flash('You can only add sections to your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    form = SectionForm()
    
    if form.validate_on_submit():
        # Get the highest order number and add 1
        last_section = Section.query.filter_by(course_id=course.id).order_by(Section.order.desc()).first()
        next_order = 1
        if last_section:
            next_order = last_section.order + 1
        
        section = Section(
            title=form.title.data,
            description=form.description.data,
            order=next_order,
            course_id=course.id
        )
        
        try:
            db.session.add(section)
            db.session.commit()
            flash('Section added successfully!', 'success')
            return redirect(url_for('main.edit_course', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating section: {e}")
            flash('An error occurred while creating the section.', 'danger')
    
    return render_template('instructor/section_editor.html', 
                          form=form, 
                          course=course,
                          is_new=True)


@main_bp.route('/instructor/section/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)
    course = Course.query.get_or_404(section.course_id)
    
    # Ensure instructor can only edit sections in their own courses
    if course.creator_id != current_user.id:
        flash('You can only edit sections in your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    form = SectionForm(obj=section)
    
    if form.validate_on_submit():
        section.title = form.title.data
        section.description = form.description.data
        
        try:
            db.session.commit()
            flash('Section updated successfully!', 'success')
            return redirect(url_for('main.edit_course', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating section: {e}")
            flash('An error occurred while updating the section.', 'danger')
    
    # Get lectures for the section
    lectures = Lecture.query.filter_by(section_id=section.id).order_by(Lecture.order).all()
    
    return render_template('instructor/section_editor.html', 
                          form=form, 
                          section=section, 
                          course=course,
                          lectures=lectures,
                          is_new=False)


@main_bp.route('/instructor/section/<int:section_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    course = Course.query.get(section.course_id)
    
    # Ensure instructor can only delete sections in their own courses
    if course.creator_id != current_user.id:
        flash('You can only delete sections in your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    try:
        # Delete associated lectures
        lectures = Lecture.query.filter_by(section_id=section.id).all()
        for lecture in lectures:
            LectureProgress.query.filter_by(lecture_id=lecture.id).delete()
            quizzes = Quiz.query.filter_by(lecture_id=lecture.id).all()
            for quiz in quizzes:
                questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
                for question in questions:
                    QuizOption.query.filter_by(question_id=question.id).delete()
                QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
                QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
                db.session.delete(quiz)
            db.session.delete(lecture)
        
        db.session.delete(section)
        
        # Reorder remaining sections
        remaining_sections = Section.query.filter_by(course_id=course.id).order_by(Section.order).all()
        for i, sec in enumerate(remaining_sections, 1):
            sec.order = i
        
        db.session.commit()
        flash('Section deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting section: {e}")
        flash('An error occurred while deleting the section.', 'danger')
    
    return redirect(url_for('main.edit_course', course_id=course.id))


@main_bp.route('/instructor/section/<int:section_id>/lecture/new', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_lecture(section_id):
    section = Section.query.get_or_404(section_id)
    course = Course.query.get(section.course_id)
    
    # Ensure instructor can only add lectures to their own courses
    if course.creator_id != current_user.id:
        flash('You can only add lectures to your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    form = LectureForm()
    
    if form.validate_on_submit():
        # Get the highest order number and add 1
        last_lecture = Lecture.query.filter_by(section_id=section.id).order_by(Lecture.order.desc()).first()
        next_order = 1
        if last_lecture:
            next_order = last_lecture.order + 1
        
        # Process YouTube URL if provided
        video_type = None
        video_id = None
        video_url = form.video_url.data
        
        if video_url:
            if 'youtube.com' in video_url or 'youtu.be' in video_url:
                video_type = 'youtube'
                video_id = extract_youtube_id(video_url)
        
        lecture = Lecture(
            title=form.title.data,
            description=form.description.data,
            video_url=video_url,
            video_type=video_type,
            video_id=video_id,
            content=form.content.data,
            duration=form.duration.data,
            order=next_order,
            section_id=section.id
        )
        
        try:
            db.session.add(lecture)
            db.session.commit()
            flash('Lecture added successfully!', 'success')
            return redirect(url_for('main.edit_section', section_id=section.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating lecture: {e}")
            flash('An error occurred while creating the lecture.', 'danger')
    
    return render_template('instructor/lecture_editor.html', 
                          form=form, 
                          section=section,
                          course=course,
                          is_new=True)


@main_bp.route('/instructor/lecture/<int:lecture_id>/edit', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Ensure instructor can only edit lectures in their own courses
    if course.creator_id != current_user.id:
        flash('You can only edit lectures in your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    form = LectureForm(obj=lecture)
    
    if form.validate_on_submit():
        lecture.title = form.title.data
        lecture.description = form.description.data
        lecture.content = form.content.data
        lecture.duration = form.duration.data
        
        # Process YouTube URL if changed
        video_url = form.video_url.data
        if video_url != lecture.video_url:
            lecture.video_url = video_url
            
            if video_url:
                if 'youtube.com' in video_url or 'youtu.be' in video_url:
                    lecture.video_type = 'youtube'
                    lecture.video_id = extract_youtube_id(video_url)
                else:
                    lecture.video_type = None
                    lecture.video_id = None
            else:
                lecture.video_type = None
                lecture.video_id = None
        
        try:
            db.session.commit()
            flash('Lecture updated successfully!', 'success')
            return redirect(url_for('main.edit_section', section_id=section.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating lecture: {e}")
            flash('An error occurred while updating the lecture.', 'danger')
    
    return render_template('instructor/lecture_editor.html', 
                          form=form, 
                          lecture=lecture,
                          section=section,
                          course=course,
                          is_new=False)


@main_bp.route('/instructor/lecture/<int:lecture_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    section = Section.query.get(lecture.section_id)
    course = Course.query.get(section.course_id)
    
    # Ensure instructor can only delete lectures in their own courses
    if course.creator_id != current_user.id:
        flash('You can only delete lectures in your own courses.', 'danger')
        return redirect(url_for('main.instructor_courses'))
    
    try:
        # Delete associated progress and quizzes
        LectureProgress.query.filter_by(lecture_id=lecture.id).delete()
        quizzes = Quiz.query.filter_by(lecture_id=lecture.id).all()
        for quiz in quizzes:
            questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
            for question in questions:
                QuizOption.query.filter_by(question_id=question.id).delete()
            QuizQuestion.query.filter_by(quiz_id=quiz.id).delete()
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            db.session.delete(quiz)
        
        db.session.delete(lecture)
        
        # Reorder remaining lectures
        remaining_lectures = Lecture.query.filter_by(section_id=section.id).order_by(Lecture.order).all()
        for i, lec in enumerate(remaining_lectures, 1):
            lec.order = i
        
        db.session.commit()
        flash('Lecture deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting lecture: {e}")
        flash('An error occurred while deleting the lecture.', 'danger')
    
    return redirect(url_for('main.edit_section', section_id=section.id))


@main_bp.route('/instructor/media', methods=['GET', 'POST'])
@login_required
@instructor_required
def media_manager():
    form = MediaUploadForm()
    
    if form.validate_on_submit():
        if form.file.data:
            if allowed_file(form.file.data.filename, ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'ppt', 'pptx']):
                try:
                    filename = save_uploaded_file(form.file.data, 'media')
                    if filename:
                        # Determine file type
                        file_type = 'document'
                        if form.file.data.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                            file_type = 'image'
                        
                        # Create media record
                        media = Media(
                            filename=form.file.data.filename,
                            file_path=filename,
                            file_type=file_type,
                            file_size=len(form.file.data.read()),
                            user_id=current_user.id
                        )
                        
                        db.session.add(media)
                        db.session.commit()
                        flash('File uploaded successfully!', 'success')
                    else:
                        flash('Failed to save the file.', 'danger')
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error uploading file: {e}")
                    flash('An error occurred during file upload.', 'danger')
            else:
                flash('File type not allowed.', 'danger')
    
    # Get all media files for this instructor
    media_files = Media.query.filter_by(user_id=current_user.id).order_by(Media.uploaded_at.desc()).all()
    
    return render_template('instructor/media_manager.html', form=form, media_files=media_files)


@main_bp.route('/instructor/media/<int:media_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_media(media_id):
    media = Media.query.get_or_404(media_id)
    
    # Ensure instructor can only delete their own media
    if media.user_id != current_user.id:
        flash('You can only delete your own media files.', 'danger')
        return redirect(url_for('main.media_manager'))
    
    try:
        # Delete the file from the filesystem
        if os.path.exists(media.file_path):
            os.remove(media.file_path)
        
        # Delete the database record
        db.session.delete(media)
        db.session.commit()
        flash('Media file deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting media: {e}")
        flash('An error occurred while deleting the media file.', 'danger')
    
    return redirect(url_for('main.media_manager'))


@main_bp.route('/instructor/get-media-for-editor')
@login_required
@instructor_required
def get_media_for_editor():
    """Returns media files in a format suitable for the rich text editor"""
    media_files = Media.query.filter_by(user_id=current_user.id, file_type='image').all()
    
    result = []
    for media in media_files:
        result.append({
            'title': media.filename,
            'value': f'/static/uploads/media/{os.path.basename(media.file_path)}'
        })
    
    return jsonify(result)


@main_bp.route('/instructor/reorder-sections', methods=['POST'])
@login_required
@instructor_required
def reorder_sections():
    """AJAX endpoint to reorder sections"""
    course_id = request.json.get('courseId')
    section_order = request.json.get('sectionOrder', [])
    
    if not course_id or not section_order:
        return jsonify({'success': False, 'message': 'Invalid data'})
    
    course = Course.query.get_or_404(course_id)
    
    # Ensure instructor can only reorder sections in their own courses
    if course.creator_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only reorder sections in your own courses'})
    
    try:
        for idx, section_id in enumerate(section_order, 1):
            section = Section.query.get(int(section_id))
            if section and section.course_id == course.id:
                section.order = idx
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering sections: {e}")
        return jsonify({'success': False, 'message': str(e)})


@main_bp.route('/instructor/reorder-lectures', methods=['POST'])
@login_required
@instructor_required
def reorder_lectures():
    """AJAX endpoint to reorder lectures"""
    section_id = request.json.get('sectionId')
    lecture_order = request.json.get('lectureOrder', [])
    
    if not section_id or not lecture_order:
        return jsonify({'success': False, 'message': 'Invalid data'})
    
    section = Section.query.get_or_404(section_id)
    course = Course.query.get(section.course_id)
    
    # Ensure instructor can only reorder lectures in their own courses
    if course.creator_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only reorder lectures in your own courses'})
    
    try:
        for idx, lecture_id in enumerate(lecture_order, 1):
            lecture = Lecture.query.get(int(lecture_id))
            if lecture and lecture.section_id == section.id:
                lecture.order = idx
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering lectures: {e}")
        return jsonify({'success': False, 'message': str(e)})


@main_bp.route('/course/<int:course_id>/modules')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    modules = Module.query.filter_by(course_id=course_id).all()
    is_enrolled = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first() is not None
    
    return render_template('view_course.html',
                         course=course,
                         modules=modules,
                         is_enrolled=is_enrolled)


@main_bp.route('/module/<int:module_id>')
@login_required
def view_module(module_id):
    module = Module.query.get_or_404(module_id)
    lessons = Lesson.query.filter_by(module_id=module_id).all()
    quiz = Quiz.query.filter_by(module_id=module_id).first()
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=module.course_id
    ).first()
    
    if not enrollment:
        flash('You must enroll in the course first.', 'error')
        return redirect(url_for('main.view_course', course_id=module.course_id))
    
    return render_template('view_module.html',
                         module=module,
                         lessons=lessons,
                         quiz=quiz)


@main_bp.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=module.course_id
    ).first()
    
    if not enrollment:
        flash('You must enroll in the course first.', 'error')
        return redirect(url_for('main.view_course', course_id=module.course_id))
    
    # Update user progress
    progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            completed=True
        )
        db.session.add(progress)
        db.session.commit()
    
    return render_template('view_lesson.html', lesson=lesson)


@main_bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    module = Module.query.get_or_404(quiz.module_id)
    
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=module.course_id
    ).first()
    
    if not enrollment:
        flash('You must enroll in the course first.', 'error')
        return redirect(url_for('main.view_course', course_id=module.course_id))
    
    if request.method == 'POST':
        score = 0
        questions = quiz.questions.all()
        total_questions = len(questions)
        
        for question in questions:
            selected_option_id = request.form.get(f'question_{question.id}')
            if selected_option_id:
                option = QuizOption.query.get(int(selected_option_id))
                if option and option.is_correct:
                    score += 1
        
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions
        )
        db.session.add(attempt)
        db.session.commit()
        
        flash(f'Quiz completed! Your score: {score}/{total_questions} ({percentage:.1f}%)', 'success')
        return redirect(url_for('main.view_module', module_id=module.id))
    
    return render_template('take_quiz.html', quiz=quiz)


@main_bp.route('/instructor/module/<int:module_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_module(module_id):
    if not current_user.is_instructor:
        flash('Access denied. Instructor access required.', 'error')
        return redirect(url_for('main.index'))
    
    module = Module.query.get_or_404(module_id)
    course = Course.query.get_or_404(module.course_id)
    
    if course.creator_id != current_user.id:
        flash('Access denied. You are not the instructor of this course.', 'error')
        return redirect(url_for('main.index'))
    
    form = ModuleForm(obj=module)
    if form.validate_on_submit():
        try:
            module.title = form.title.data
            module.description = form.description.data
            db.session.commit()
            flash('Module updated successfully!', 'success')
            return redirect(url_for('main.view_course', course_id=course.id))
        except Exception as e:
            current_app.logger.error(f"Error updating module: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the module.', 'error')
    
    return render_template('edit_module.html', form=form, module=module)


@main_bp.route('/instructor/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    if not current_user.is_instructor:
        flash('Access denied. Instructor access required.', 'error')
        return redirect(url_for('main.index'))
    
    lesson = Lesson.query.get_or_404(lesson_id)
    module = Module.query.get_or_404(lesson.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    if course.creator_id != current_user.id:
        flash('Access denied. You are not the instructor of this course.', 'error')
        return redirect(url_for('main.index'))
    
    form = LessonForm(obj=lesson)
    if form.validate_on_submit():
        try:
            lesson.title = form.title.data
            lesson.content = form.content.data
            db.session.commit()
            flash('Lesson updated successfully!', 'success')
            return redirect(url_for('main.view_module', module_id=module.id))
        except Exception as e:
            current_app.logger.error(f"Error updating lesson: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the lesson.', 'error')
    
    return render_template('edit_lesson.html', form=form, lesson=lesson)


@main_bp.route('/instructor/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not current_user.is_instructor:
        flash('Access denied. Instructor access required.', 'error')
        return redirect(url_for('main.index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    module = Module.query.get_or_404(quiz.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    if course.creator_id != current_user.id:
        flash('Access denied. You are not the instructor of this course.', 'error')
        return redirect(url_for('main.index'))
    
    form = QuizForm(obj=quiz)
    if form.validate_on_submit():
        try:
            quiz.title = form.title.data
            quiz.description = form.description.data
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('main.view_module', module_id=module.id))
        except Exception as e:
            current_app.logger.error(f"Error updating quiz: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the quiz.', 'error')
    
    return render_template('edit_quiz.html', form=form, quiz=quiz)


@main_bp.route('/instructor/quiz/<int:quiz_id>/question/add', methods=['GET', 'POST'])
@login_required
def add_quiz_question(quiz_id):
    if not current_user.is_instructor:
        flash('Access denied. Instructor access required.', 'error')
        return redirect(url_for('main.index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    module = Module.query.get_or_404(quiz.module_id)
    course = Course.query.get_or_404(module.course_id)
    
    if course.creator_id != current_user.id:
        flash('Access denied. You are not the instructor of this course.', 'error')
        return redirect(url_for('main.index'))
    
    form = QuizQuestionForm()
    if form.validate_on_submit():
        try:
            # Create the question
            question = QuizQuestion(
                quiz_id=quiz_id,
                question=form.question.data
            )
            db.session.add(question)
            db.session.flush()  # Get the question ID
            
            # Parse options (one per line) and create QuizOption objects
            options_text = form.options.data.strip().split('\n')
            correct_option_num = form.correct_option.data
            
            for idx, option_text in enumerate(options_text, 1):
                option_text = option_text.strip()
                if option_text:  # Skip empty lines
                    option = QuizOption(
                        option_text=option_text,
                        is_correct=(idx == correct_option_num),
                        question_id=question.id
                    )
                    db.session.add(option)
            
            db.session.commit()
            flash('Question added successfully!', 'success')
            return redirect(url_for('main.edit_quiz', quiz_id=quiz_id))
        except Exception as e:
            current_app.logger.error(f"Error adding quiz question: {str(e)}")
            db.session.rollback()
            flash('An error occurred while adding the question.', 'error')
    
    return render_template('add_quiz_question.html', form=form, quiz=quiz)
