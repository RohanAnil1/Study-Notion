import os
import uuid
import re
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename, file_type='image'):
    """Check if the file extension is allowed based on file type."""
    if not '.' in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    elif file_type == 'document':
        return ext in current_app.config['ALLOWED_DOCUMENT_EXTENSIONS']
    return False

def get_upload_folder(folder_type):
    """Get the appropriate upload folder based on type."""
    base_folder = current_app.config['UPLOAD_FOLDER']
    if folder_type == 'course_thumbnail':
        return os.path.join(base_folder, current_app.config['COURSE_THUMBNAILS_FOLDER'])
    elif folder_type == 'profile_pic':
        return os.path.join(base_folder, current_app.config['PROFILE_PICS_FOLDER'])
    elif folder_type == 'media':
        return os.path.join(base_folder, current_app.config['MEDIA_FOLDER'])
    return base_folder

def save_uploaded_file(file, folder_type='course_thumbnail', file_type='image'):
    """
    Save an uploaded file with proper validation and organization.
    
    Args:
        file: The uploaded file object
        folder_type: Type of upload (course_thumbnail, profile_pic, media)
        file_type: Type of file (image, document)
    
    Returns:
        tuple: (success: bool, message: str, file_path: str)
    """
    if not file:
        return False, "No file provided", None
    
    if not allowed_file(file.filename, file_type):
        return False, f"File type not allowed. Allowed types: {', '.join(current_app.config[f'ALLOWED_{file_type.upper()}_EXTENSIONS'])}", None
    
    # Check file size
    max_size = current_app.config[f'MAX_{file_type.upper()}_SIZE']
    if len(file.read()) > max_size:
        file.seek(0)  # Reset file pointer
        return False, f"File too large. Maximum size is {max_size/1024/1024}MB", None
    file.seek(0)  # Reset file pointer
    
    try:
        # Create upload directory if it doesn't exist
        upload_folder = get_upload_folder(folder_type)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Set appropriate permissions
        os.chmod(file_path, 0o644)
        
        # Return relative path with forward slashes for web URLs
        relative_path = os.path.join('uploads', os.path.basename(upload_folder), unique_filename).replace('\\', '/')
        
        logger.info(f"File saved successfully: {relative_path}")
        return True, "File uploaded successfully", relative_path
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False, f"Error saving file: {str(e)}", None

def delete_uploaded_file(file_path):
    """
    Delete an uploaded file.
    
    Args:
        file_path: The relative path of the file to delete
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not file_path:
        return True, "No file to delete"
    
    try:
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True, "File deleted successfully"
        return True, "File does not exist"
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False, f"Error deleting file: {str(e)}"

def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if not url:
        return None
        
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None

def format_datetime(date):
    """Format datetime for display"""
    if not date:
        return "N/A"
    return date.strftime("%B %d, %Y at %I:%M %p")

def seconds_to_time_format(seconds):
    """Convert seconds to HH:MM:SS format"""
    if not seconds:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
