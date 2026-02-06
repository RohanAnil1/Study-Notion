import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Compute absolute path for SQLite database
basedir = os.path.dirname(os.path.abspath(__file__))

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration - always use absolute path
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    COURSE_THUMBNAILS_FOLDER = 'course_thumbnails'
    PROFILE_PICS_FOLDER = 'profile_pics'
    MEDIA_FOLDER = 'media'
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB max image size
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB max document size 