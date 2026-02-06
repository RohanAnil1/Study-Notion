from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, IntegerField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = RadioField('Account Type', choices=[('student', 'Student'), ('instructor', 'Instructor')], default='student')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_pic = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Course Description', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    thumbnail = FileField('Course Thumbnail', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    is_published = BooleanField('Publish Course', default=False)

class SectionForm(FlaskForm):
    title = StringField('Section Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Section Description', validators=[Optional()])

class LectureForm(FlaskForm):
    title = StringField('Lecture Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Lecture Description', validators=[Optional()])
    video_url = StringField('Video URL', validators=[Optional()])
    content = TextAreaField('Lecture Content', validators=[Optional()], 
        description="Use the rich text editor to add formatted text, images, and other content.")
    duration = IntegerField('Duration (in minutes)', default=0, validators=[Optional()])

class MediaUploadForm(FlaskForm):
    file = FileField('File', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'ppt', 'pptx'], 
                    'Allowed file types: images, PDF, Office documents')
    ])
    description = StringField('Description', validators=[Optional()])

class QuizGeneratorForm(FlaskForm):
    num_questions = IntegerField('Number of Questions', default=5, validators=[DataRequired()])
    generate_new = BooleanField('Generate New Quiz (will replace existing)', default=False)

class ModuleForm(FlaskForm):
    title = StringField('Module Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Module Description', validators=[Optional()])
    order = IntegerField('Order', default=0, validators=[Optional()])

class LessonForm(FlaskForm):
    title = StringField('Lesson Title', validators=[DataRequired(), Length(max=128)])
    content = TextAreaField('Lesson Content', validators=[DataRequired()])
    order = IntegerField('Order', default=0, validators=[Optional()])

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Quiz Description', validators=[Optional()])

class QuizQuestionForm(FlaskForm):
    question = TextAreaField('Question', validators=[DataRequired()])
    options = TextAreaField('Options (one per line)', validators=[DataRequired()])
    correct_option = IntegerField('Correct Option Number', validators=[DataRequired()])
