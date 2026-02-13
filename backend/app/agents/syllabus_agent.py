
from langchain_google_genai import GoogleGenerativeAI
import json
import logging

logger = logging.getLogger(__name__)
llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.3)

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
        # Truncate text if too long to stay within token limits
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n[... content truncated due to length ...]"
        
        response = llm.invoke(PROMPT + text)
        
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
        return {
            "error": str(e),
            "units": [
                {
                    "unit_id": 1,
                    "unit_name": "Processing Error",
                    "description": "Failed to analyze syllabus",
                    "topics": []
                }
            ]
        }
