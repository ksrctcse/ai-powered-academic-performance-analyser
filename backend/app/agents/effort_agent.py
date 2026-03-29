"""
Effort and time estimation agent using Google Generative AI.
Calculates learning effort hours and end dates based on concept complexity.
"""

from langchain_google_genai import GoogleGenerativeAI
import json
import os
from dotenv import load_dotenv
from ..core.logger import get_logger
from datetime import datetime, timedelta

load_dotenv()
logger = get_logger(__name__)

# Lazy initialization - only create LLM when calculate_effort() is called
_llm = None

def get_llm():
    """Get or create LLM instance (lazy loading)"""
    global _llm
    if _llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your-google-api-key":
            raise ValueError(
                "GOOGLE_API_KEY not configured. "
                "Please set the GOOGLE_API_KEY environment variable in .env file."
            )
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3)
    return _llm

EFFORT_PROMPT = """Analyze the following concepts and their complexity levels. 
Calculate the total estimated learning effort in hours for a student to master these concepts.

Consider:
- LOW complexity: 2-4 hours
- MEDIUM complexity: 4-8 hours  
- HIGH complexity: 8-16 hours

Return ONLY a JSON object with this exact structure, no other text:
{
  "total_hours": <number>,
  "concepts_breakdown": [
    {"concept": "name", "hours": <number>, "complexity": "LEVEL"}
  ],
  "average_complexity": "<LOW|MEDIUM|HIGH>" 
}

Concepts to analyze:
"""


def calculate_effort(concepts: list) -> dict:
    """
    Calculate learning effort for a list of concepts.
    
    Args:
        concepts: List of dictionaries with {name, complexity} 
                 e.g., [{"name": "Concept1", "complexity": "MEDIUM"}]
    
    Returns:
        Dictionary with {
            total_hours: float,
            concepts_breakdown: list,
            average_complexity: str,
            error: str (if any)
        }
    """
    try:
        if not concepts:
            return {
                "total_hours": 0,
                "concepts_breakdown": [],
                "average_complexity": "LOW",
                "error": "No concepts provided"
            }
        
        # Format concepts for prompt
        concepts_text = json.dumps(concepts, indent=2)
        prompt = EFFORT_PROMPT + concepts_text
        
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Parse JSON response
        # Find JSON in response (in case there's extra text)
        response_text = response.strip()
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            logger.warning(f"Invalid JSON response from effort agent: {response_text}")
            return _default_effort_calculation(concepts)
        
        json_str = response_text[start_idx:end_idx]
        result = json.loads(json_str)
        
        # Validate required fields
        if "total_hours" not in result or "average_complexity" not in result:
            logger.warning(f"Missing required fields in effort response: {result}")
            return _default_effort_calculation(concepts)
        
        logger.info(f"Effort calculation successful: {result['total_hours']} hours, {result['average_complexity']} complexity")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in effort calculation: {str(e)}", exc_info=True)
        return _default_effort_calculation(concepts)
    except Exception as e:
        logger.error(f"Error calculating effort: {str(e)}", exc_info=True)
        return _default_effort_calculation(concepts)


def _default_effort_calculation(concepts: list) -> dict:
    """
    Default effort calculation based on complexity levels.
    Used when AI service is unavailable.
    """
    effort_map = {
        "LOW": 3,
        "MEDIUM": 6,
        "HIGH": 12
    }
    
    total_hours = 0
    complexities = []
    breakdown = []
    
    for concept in concepts:
        complexity = concept.get("complexity", "MEDIUM").upper()
        hours = effort_map.get(complexity, 6)
        total_hours += hours
        complexities.append(complexity)
        breakdown.append({
            "concept": concept.get("name", "Unknown"),
            "hours": hours,
            "complexity": complexity
        })
    
    # Calculate average complexity
    complexity_values = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    avg_value = sum(complexity_values.get(c, 2) for c in complexities) / len(complexities) if complexities else 2
    
    if avg_value < 1.5:
        avg_complexity = "LOW"
    elif avg_value < 2.5:
        avg_complexity = "MEDIUM"
    else:
        avg_complexity = "HIGH"
    
    return {
        "total_hours": total_hours,
        "concepts_breakdown": breakdown,
        "average_complexity": avg_complexity
    }


def calculate_end_date(start_date_str: str, effort_hours: float) -> str:
    """
    Calculate end date based on start date and effort hours.
    Assumes 4 hours of learning per day.
    
    Args:
        start_date_str: ISO format date string (e.g., "2024-03-01")
        effort_hours: Total learning hours
    
    Returns:
        ISO format end date string
    """
    try:
        if not start_date_str:
            start_date = datetime.now()
        else:
            # Parse ISO format date
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        # Calculate days needed (4 hours per day)
        days_needed = effort_hours / 4
        end_date = start_date + timedelta(days=days_needed)
        
        return end_date.isoformat()
    except Exception as e:
        logger.error(f"Error calculating end date: {str(e)}", exc_info=True)
        # Fallback: add 7 days
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        return end_date.isoformat()
