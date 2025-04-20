import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import json
from ai_services import generate_course_content
import time
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_course_with_retry(title, description, num_modules):
    try:
        return generate_course_content(title, description, num_modules)
    except Exception as e:
        logger.error(f"Attempt failed: {str(e)}")
        raise

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get('GEMINI_API_KEY')
    logger.info(f"API Key found: {bool(api_key)}")
    
    if not api_key:
        logger.error("No API key found in environment variables")
        return
        
    try:
        # Configure the API
        genai.configure(api_key=api_key, transport="rest")
        logger.info("Gemini API configured successfully")
        
        # Test course content generation
        title = "Python Basics"
        description = "Learn the fundamentals of Python programming."
        
        logger.info(f"Generating course content for: {title}")
        course = generate_course_with_retry(title, description, num_modules=2)
        
        if course and 'modules' in course:
            logger.info("Course content generated successfully!")
            
            # Save the response to a file for inspection
            with open('course_content_response.json', 'w') as f:
                json.dump(course, f, indent=2)
            logger.info("Course content saved to course_content_response.json")
            
            # Print each module
            for i, module in enumerate(course['modules'], 1):
                logger.info(f"\nModule {i}: {module['title']}")
                logger.info(f"Description: {module['description']}")
                logger.info("\nLessons:")
                
                for j, lesson in enumerate(module['lessons'], 1):
                    logger.info(f"\n  {j}. {lesson['title']}")
                    # Truncate content to first 200 characters
                    content_preview = lesson['content'][:200] + "..." if len(lesson['content']) > 200 else lesson['content']
                    logger.info(f"     {content_preview}")
        else:
            logger.error("Course content generation failed - invalid response format")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main() 