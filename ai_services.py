"""
AI Services module for the Learning Platform.
Provides integration with Google's Gemini AI for generating quizzes, summaries, and study notes.
"""

import os
import logging
import json
try:
    import google.generativeai as genai
except Exception:
    genai = None
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Configure the Gemini API
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    logger.info(f"API Key found: {bool(api_key)}")
    
    if genai and api_key and api_key != "your_new_api_key_here":
        # Configure with API version v1
        genai.configure(api_key=api_key, transport="rest")
        logger.info("Gemini API configured successfully")
        
        # Check if the API is working by listing available models
        try:
            models = genai.list_models()
            model_names = [model.name for model in models]
            logger.info(f"Available Gemini models: {model_names}")
            
            # Find a suitable model - prefer the newer models
            if "models/gemini-1.5-flash" in model_names:
                MODEL = "models/gemini-1.5-flash"
                MODEL_AVAILABLE = True
                logger.info("Using gemini-1.5-flash model")
            elif "models/gemini-1.5-pro" in model_names:
                MODEL = "models/gemini-1.5-pro"
                MODEL_AVAILABLE = True
                logger.info("Using gemini-1.5-pro model")
            # Avoid deprecated models
            elif any("gemini" in name and "1.0" not in name for name in model_names):
                # Use the first available non-deprecated Gemini model
                MODEL = next(name for name in model_names if "gemini" in name and "1.0" not in name)
                MODEL_AVAILABLE = True
                logger.info(f"Using fallback model: {MODEL}")
            else:
                logger.warning("No suitable Gemini model found. AI features will be disabled.")
                MODEL_AVAILABLE = False
                MODEL = None
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            MODEL_AVAILABLE = False
            MODEL = None
    else:
        logger.warning("No valid Gemini API key found. AI features will be disabled.")
        MODEL_AVAILABLE = False
        MODEL = None
except Exception as e:
    logger.error(f"Error configuring Gemini API: {str(e)}")
    MODEL_AVAILABLE = False
    MODEL = None

def generate_quiz_from_content(content, num_questions=5):
    """
    Generate a quiz with questions based on the provided content using Google's Gemini.
    
    Args:
        content (str): The lecture content to generate questions from
        num_questions (int): Number of questions to generate
        
    Returns:
        dict: A dictionary containing quiz questions and answers
    """
    if not MODEL_AVAILABLE:
        logger.warning("Gemini API not available. Using fallback quiz generation.")
        return _generate_fallback_quiz(content, num_questions)
    
    try:
        # Create a system prompt for quiz generation
        prompt = f"""
        Generate a multiple-choice quiz with {num_questions} questions based on the following content:
        
        {content}
        
        For each question:
        1. Create a clear, concise question
        2. Provide 4 possible answers, with exactly one correct answer
        3. Indicate which answer is correct
        
        Format your response as a JSON structure with this exact schema:
        {{
            "questions": [
                {{
                    "question": "The question text",
                    "options": [
                        {{ "text": "Option A", "is_correct": false }},
                        {{ "text": "Option B", "is_correct": true }},
                        {{ "text": "Option C", "is_correct": false }},
                        {{ "text": "Option D", "is_correct": false }}
                    ]
                }}
            ]
        }}
        
        Each question should have exactly one correct answer. The questions should test understanding, not just recall.
        """
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        
        # Extract the JSON content from the response
        response_text = response.text
        # Find the JSON part of the response (it might be wrapped in markdown code blocks)
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_text = response_text.strip()
            
        # Parse the JSON
        quiz_data = json.loads(json_text)
        return quiz_data
        
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        return _generate_fallback_quiz(content, num_questions)

def summarize_content(content):
    """
    Generate a concise summary of the provided content using Google's Gemini.
    
    Args:
        content (str): The content to summarize
        
    Returns:
        str: A summary of the content
    """
    if not MODEL_AVAILABLE:
        logger.warning("Gemini API not available. Using fallback summarization.")
        return _generate_fallback_summary(content)
    
    try:
        # Create a system prompt for summarization
        prompt = f"""
        Please provide a concise summary of the following content:
        
        {content}
        
        The summary should:
        1. Be approximately 3-5 paragraphs
        2. Highlight the key concepts and main points
        3. Include important details, definitions, and examples
        4. Be well-structured with clear organization
        """
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return _generate_fallback_summary(content)

def generate_study_notes(content):
    """
    Generate study notes from the provided content using Google's Gemini.
    
    Args:
        content (str): The content to generate study notes from
        
    Returns:
        str: Structured study notes
    """
    if not MODEL_AVAILABLE:
        logger.warning("Gemini API not available. Using fallback study notes.")
        return _generate_fallback_study_notes(content)
    
    try:
        logger.info("Starting study notes generation")
        # Create a system prompt for study notes generation
        prompt = f"""
        Create comprehensive study notes based on the following content:
        
        {content}
        
        The study notes should:
        1. Begin with a high-level overview of the main topic
        2. Break down the content into clear sections with headings
        3. Include bullet points for key concepts and definitions
        4. Highlight important relationships between concepts
        5. Include examples where relevant
        6. End with a brief summary of the most critical points to remember
        
        Format the notes in markdown with clear headings, bullet points, and emphasis on key terms.
        """
        
        logger.info(f"Using model: {MODEL}")
        model = genai.GenerativeModel(MODEL)
        logger.info("Model initialized, generating content...")
        response = model.generate_content(prompt)
        logger.info("Content generated successfully")
        
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Error generating study notes: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return _generate_fallback_study_notes(content)

def generate_course_content(title, description, num_modules=5):
    """
    Generate a structured course outline with modules and lessons using Google's Gemini.
    
    Args:
        title (str): The course title
        description (str): The course description
        num_modules (int): Number of modules to generate
        
    Returns:
        dict: A dictionary containing the course structure with modules and lessons
    """
    if not MODEL_AVAILABLE:
        logger.warning("Gemini API not available. Using fallback course content.")
        return _generate_fallback_course_content(title, description, num_modules)
    
    try:
        # Create a system prompt for course content generation
        prompt = f"""
        Generate a detailed course structure for a course with the following details:
        
        Title: {title}
        Description: {description}
        Number of Modules: {num_modules}
        
        For each module:
        1. Create a clear title that reflects its content
        2. Write a brief description of the module
        3. Include 3-5 lessons per module
        4. For each lesson, provide a title and brief content outline
        
        Format your response as a JSON structure with this exact schema:
        {{
            "modules": [
                {{
                    "title": "Module title",
                    "description": "Module description",
                    "order": 1,
                    "lessons": [
                        {{
                            "title": "Lesson title",
                            "content": "Lesson content outline",
                            "order": 1
                        }}
                    ]
                }}
            ]
        }}
        
        The content should be logically structured with clear progression from basic to advanced concepts.
        """
        
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        
        # Extract the JSON content from the response
        response_text = response.text
        # Find the JSON part of the response (it might be wrapped in markdown code blocks)
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_text = response_text.strip()
            
        # Parse the JSON
        course_data = json.loads(json_text)
        return course_data
        
    except Exception as e:
        logger.error(f"Error generating course content: {e}")
        return _generate_fallback_course_content(title, description, num_modules)

# Fallback functions for when the AI service is unavailable
def _generate_fallback_quiz(content, num_questions=5):
    """
    Generate a better fallback quiz when AI services are unavailable.
    This includes some actual sample questions based on common programming topics.
    """
    # Try to extract keywords from the content to make more relevant fallback questions
    keywords = ["python", "javascript", "programming", "database", "web", "html", 
                "css", "function", "class", "algorithm", "react", "flask"]
    
    found_keywords = [k for k in keywords if k in content.lower()]
    
    if "python" in found_keywords:
        return {
            "questions": [
                {
                    "question": "What is Python's primary programming paradigm?",
                    "options": [
                        {"text": "Object-oriented programming", "is_correct": True},
                        {"text": "Procedural programming only", "is_correct": False},
                        {"text": "Functional programming only", "is_correct": False},
                        {"text": "Assembly programming", "is_correct": False}
                    ]
                },
                {
                    "question": "Which of the following is a correct way to create a list in Python?",
                    "options": [
                        {"text": "my_list = [1, 2, 3]", "is_correct": True},
                        {"text": "my_list = (1, 2, 3)", "is_correct": False},
                        {"text": "my_list = {1, 2, 3}", "is_correct": False},
                        {"text": "my_list = 1, 2, 3", "is_correct": False}
                    ]
                },
                {
                    "question": "What does the 'self' parameter in Python class methods represent?",
                    "options": [
                        {"text": "The instance of the class", "is_correct": True},
                        {"text": "The class itself", "is_correct": False},
                        {"text": "The parent class", "is_correct": False},
                        {"text": "A required keyword", "is_correct": False}
                    ]
                }
            ]
        }
    elif "javascript" in found_keywords or "web" in found_keywords:
        return {
            "questions": [
                {
                    "question": "Which of the following is used to declare a variable in modern JavaScript?",
                    "options": [
                        {"text": "let and const", "is_correct": True},
                        {"text": "dim", "is_correct": False},
                        {"text": "define", "is_correct": False},
                        {"text": "int and string", "is_correct": False}
                    ]
                },
                {
                    "question": "What does the DOM stand for in web development?",
                    "options": [
                        {"text": "Document Object Model", "is_correct": True},
                        {"text": "Data Object Model", "is_correct": False},
                        {"text": "Document Oriented Markup", "is_correct": False},
                        {"text": "Display Object Management", "is_correct": False}
                    ]
                }
            ]
        }
    else:
        # Default generic programming questions
        return {
            "questions": [
                {
                    "question": "What is a function in programming?",
                    "options": [
                        {"text": "A reusable block of code that performs a specific task", "is_correct": True},
                        {"text": "A type of variable", "is_correct": False},
                        {"text": "A database query", "is_correct": False},
                        {"text": "A hardware component", "is_correct": False}
                    ]
                },
                {
                    "question": "Which data structure follows the LIFO (Last In, First Out) principle?",
                    "options": [
                        {"text": "Stack", "is_correct": True},
                        {"text": "Queue", "is_correct": False},
                        {"text": "Tree", "is_correct": False},
                        {"text": "Graph", "is_correct": False}
                    ]
                },
                {
                    "question": "What does API stand for?",
                    "options": [
                        {"text": "Application Programming Interface", "is_correct": True},
                        {"text": "Automated Programming Interface", "is_correct": False},
                        {"text": "Application Process Integration", "is_correct": False},
                        {"text": "Algorithmic Programming Interface", "is_correct": False}
                    ]
                }
            ]
        }

def _generate_fallback_summary(content):
    """
    Generate a better fallback summary when AI services are unavailable.
    This extracts some content from the lecture to provide a simple summary.
    """
    # Extract the first 2-3 sentences if possible
    sentences = content.split('.')
    if len(sentences) > 3:
        intro = '. '.join(sentences[:3]) + '.'
    else:
        intro = content[:200] + '...' if len(content) > 200 else content
    
    # Remove HTML tags for cleaner output
    intro = intro.replace('<p>', '').replace('</p>', '\n\n')
    intro = intro.replace('<h1>', '# ').replace('</h1>', '\n\n')
    intro = intro.replace('<h2>', '## ').replace('</h2>', '\n\n')
    intro = intro.replace('<h3>', '### ').replace('</h3>', '\n\n')
    intro = intro.replace('<ul>', '').replace('</ul>', '')
    intro = intro.replace('<li>', '- ').replace('</li>', '\n')
    
    return f"""
    # Content Summary 
    
    This is a basic summary extracted from the lecture content:
    
    {intro}
    
    Note: For more comprehensive AI-generated summaries, please ensure the Gemini API key is correctly configured.
    """

def _generate_fallback_study_notes(content):
    """Generate basic study notes when AI services are unavailable."""
    return """
# Study Notes

## Overview
This is a basic overview of the content.

## Key Points
* Important point 1
* Important point 2
* Important point 3

## Summary
These are the most important concepts to remember from this content.
"""

def _generate_fallback_course_content(title, description, num_modules=5):
    """
    Generate a basic course structure when AI services are unavailable.
    
    Args:
        title (str): The course title
        description (str): The course description
        num_modules (int): Number of modules to generate
        
    Returns:
        dict: A dictionary containing a basic course structure
    """
    modules = []
    
    # Create a basic module structure
    for i in range(1, num_modules + 1):
        module = {
            "title": f"Module {i}",
            "description": f"This is module {i} of the {title} course.",
            "order": i,
            "lessons": []
        }
        
        # Add 3 lessons to each module
        for j in range(1, 4):
            lesson = {
                "title": f"Lesson {j}",
                "content": f"Content outline for lesson {j} of module {i}.",
                "order": j
            }
            module["lessons"].append(lesson)
            
        modules.append(module)
    
    return {"modules": modules}