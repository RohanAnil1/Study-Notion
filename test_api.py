import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import json
from ai_services import (
    generate_study_notes,
    generate_quiz_from_content,
    summarize_content,
    generate_course_content
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_study_notes():
    logger.info("\n=== Testing Study Notes Generation ===")
    sample_content = """
    Python is a high-level, interpreted programming language. It emphasizes code readability with its notable use of significant whitespace.
    Key features of Python include:
    1. Dynamic typing
    2. Object-oriented programming support
    3. Extensive standard library
    4. Rich ecosystem of third-party packages
    """
    try:
        notes = generate_study_notes(sample_content)
        logger.info("Study notes generated successfully:")
        logger.info(notes[:500] + "..." if len(notes) > 500 else notes)
    except Exception as e:
        logger.error(f"Error in study notes generation: {str(e)}")

def test_quiz_generation():
    logger.info("\n=== Testing Quiz Generation ===")
    sample_content = """
    Flask is a lightweight WSGI web application framework in Python. It is designed to be simple and easy to use.
    Key concepts in Flask include:
    - Routes: Define URL patterns and handling functions
    - Templates: Use Jinja2 for dynamic HTML generation
    - Extensions: Add functionality through Flask extensions
    - Blueprints: Organize application into modular components
    """
    try:
        quiz = generate_quiz_from_content(sample_content, num_questions=3)
        logger.info("Quiz generated successfully:")
        logger.info(json.dumps(quiz, indent=2))
    except Exception as e:
        logger.error(f"Error in quiz generation: {str(e)}")

def test_content_summary():
    logger.info("\n=== Testing Content Summarization ===")
    sample_content = """
    Machine Learning is a subset of artificial intelligence that focuses on developing systems that can learn from and make decisions based on data.
    The main types of machine learning are:
    1. Supervised Learning: Models learn from labeled training data
    2. Unsupervised Learning: Models find patterns in unlabeled data
    3. Reinforcement Learning: Models learn through trial and error with rewards/penalties
    4. Deep Learning: Models use neural networks with multiple layers
    Each type has its own applications and use cases in real-world scenarios.
    """
    try:
        summary = summarize_content(sample_content)
        logger.info("Content summary generated successfully:")
        logger.info(summary)
    except Exception as e:
        logger.error(f"Error in content summarization: {str(e)}")

def test_course_content():
    logger.info("\n=== Testing Course Content Generation ===")
    title = "Introduction to Python"
    description = "A beginner's guide to Python programming fundamentals."
    try:
        course = generate_course_content(title, description, num_modules=2)
        logger.info("Course content generated successfully:")
        # Print each module separately to avoid output truncation
        for i, module in enumerate(course.get('modules', []), 1):
            logger.info(f"\nModule {i}:")
            logger.info(f"Title: {module.get('title')}")
            logger.info(f"Description: {module.get('description')}")
            logger.info("Lessons:")
            for j, lesson in enumerate(module.get('lessons', []), 1):
                logger.info(f"  {j}. {lesson.get('title')}")
                logger.info(f"     Content: {lesson.get('content')[:200]}...")
    except Exception as e:
        logger.error(f"Error in course content generation: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get('GEMINI_API_KEY')
    logger.info(f"API Key found: {bool(api_key)}")
    
    if api_key:
        try:
            # Configure the API
            genai.configure(api_key=api_key, transport="rest")
            logger.info("Gemini API configured successfully")
            
            # Run all tests
            test_study_notes()
            test_quiz_generation()
            test_content_summary()
            test_course_content()
            
        except Exception as e:
            logger.error(f"Error in API configuration: {str(e)}")
    else:
        logger.error("No API key found in environment variables") 