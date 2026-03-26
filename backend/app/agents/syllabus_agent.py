
from langchain_google_genai import GoogleGenerativeAI
import json
import logging
import os
from threading import Thread
import signal

logger = logging.getLogger(__name__)

# Lazy initialization - only create LLM when analyze() is called
_llm = None

def get_llm():
    """Get or create LLM instance (lazy loading)"""
    global _llm
    if _llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your-google-api-key":
            raise ValueError(
                "GOOGLE_API_KEY not configured. "
                "Please set the GOOGLE_API_KEY environment variable in .env file. "
                "Get your key from: https://makersuite.google.com/app/apikey"
            )
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3, timeout=120)
    return _llm


PROMPT = '''
Analyze the provided syllabus text and extract a hierarchical structure.
Return ONLY valid JSON with this exact format (no other text):
{
  "course_title": "Course Name",
  "units": [
    {
      "unit_id": 1,
      "unit_name": "Unit Name",
      "description": "Brief description",
      "topics": [
        {
          "topic_id": 1,
          "topic_name": "Topic Name",
          "concepts": ["Concept 1", "Concept 2", "Concept 3"]
        }
      ]
    }
  ]
}

Rules:
- Each unit must have unit_id, unit_name, description, and topics array
- Each topic must have topic_id, topic_name, and concepts array
- Concepts should be atomic, specific terms from the syllabus
- Extract ALL units and topics from the syllabus
- If no clear structure exists, infer logical groupings
- Return ONLY JSON, no markdown formatting or code blocks

Syllabus content:
'''

def analyze(text):
    """
    Analyze syllabus text and extract hierarchical structure (units -> topics -> concepts).
    
    Args:
        text: The raw syllabus text to analyze
        
    Returns:
        dict: Structured analysis with units, topics, and concepts, or error message
    """
    try:
        # Get LLM instance (lazy loading)
        llm = get_llm()
        
        # Truncate text if too long to stay within token limits
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n[... content truncated due to length ...]"
        
        # Use timeout for the LLM call (30 seconds)
        import signal
        from contextlib import contextmanager
        
        @contextmanager
        def timeout_context(seconds):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Analysis took longer than {seconds} seconds")
            
            # Only set signal on Unix systems
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        try:
            with timeout_context(120):  # 120 second timeout for analysis
                response = llm.invoke(PROMPT + text)
        except TimeoutError:
            logger.warning("Syllabus analysis timed out after 120 seconds, returning fallback structure")
            return {
                "course_title": "Imported Syllabus",
                "units": [
                    {
                        "unit_id": 1,
                        "unit_name": "General Content",
                        "description": "Content extracted from syllabus",
                        "topics": [
                            {
                                "topic_id": 1,
                                "topic_name": "Syllabus Content",
                                "concepts": ["See analysis_result for details"]
                            }
                        ]
                    }
                ],
                "note": "Analysis timed out - using fallback structure"
            }
        
        # Parse response
        if isinstance(response, str):
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {str(e)}")
                # Return a fallback structure with raw text
                return {
                    "course_title": "Imported Syllabus",
                    "units": [
                        {
                            "unit_id": 1,
                            "unit_name": "General Content",
                            "description": "Content extracted from syllabus",
                            "topics": [
                                {
                                    "topic_id": 1,
                                    "topic_name": "Syllabus Content",
                                    "concepts": ["See analysis_result for details"]
                                }
                            ]
                        }
                    ],
                    "raw_response": response_text[:500]
                }
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing syllabus: {str(e)}", exc_info=True)
        # Log the text length to help debug
        logger.error(f"Input text length: {len(text) if text else 0} characters")
        if text:
            logger.debug(f"First 500 chars of text: {text[:500]}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "units": [
                {
                    "unit_id": 1,
                    "unit_name": "Processing Error",
                    "description": f"Failed to analyze syllabus: {str(e)[:100]}",
                    "topics": []
                }
            ]
        }
