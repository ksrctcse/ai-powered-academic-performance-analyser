from langchain_google_genai import GoogleGenerativeAI
import json
from app.core.logger import get_logger

logger = get_logger(__name__)

llm = GoogleGenerativeAI(model="gemini-2.5-pro")

COMPLEXITY_PROMPT = """Analyze the following concept and classify its complexity level.
Return ONLY one of: LOW, MEDIUM, HIGH
Concept: """


def classify(concept: str) -> str:
    """
    Classify a single concept's complexity level.
    
    Args:
        concept: The concept name/description to analyze
        
    Returns:
        A complexity level: LOW, MEDIUM, or HIGH
    """
    try:
        response = llm.invoke(COMPLEXITY_PROMPT + concept)
        # Extract first line and clean it
        complexity = response.strip().split('\n')[0].upper()
        # Validate the response
        if complexity in ["LOW", "MEDIUM", "HIGH"]:
            return complexity
        else:
            logger.warning(f"Invalid complexity response '{complexity}' for concept '{concept}', defaulting to MEDIUM")
            return "MEDIUM"
    except Exception as e:
        logger.error(f"Error classifying complexity for concept '{concept}': {str(e)}", exc_info=True)
        return "MEDIUM"  # Default to MEDIUM on error


def analyze_hierarchy_complexity(hierarchy: dict) -> dict:
    """
    Analyze complexity for all concepts in a hierarchical structure.
    
    Args:
        hierarchy: Dictionary with structure {course_title: str, units: [{unit_name, topics: [{topic_name, concepts: []}]}]}
        
    Returns:
        Same structure with complexity_level added to each concept
    """
    if not hierarchy or "units" not in hierarchy:
        return hierarchy
    
    try:
        analyzed_hierarchy = {
            "course_title": hierarchy.get("course_title", ""),
            "units": []
        }
        
        for unit in hierarchy.get("units", []):
            analyzed_unit = {
                "unit_id": unit.get("unit_id"),
                "unit_name": unit.get("unit_name"),
                "description": unit.get("description"),
                "topics": []
            }
            
            for topic in unit.get("topics", []):
                analyzed_topic = {
                    "topic_id": topic.get("topic_id"),
                    "topic_name": topic.get("topic_name"),
                    "concepts": []
                }
                
                for concept in topic.get("concepts", []):
                    if isinstance(concept, dict):
                        concept_name = concept.get("name", concept.get("concept_name", ""))
                    else:
                        concept_name = str(concept)
                    
                    complexity = classify(concept_name)
                    analyzed_topic["concepts"].append({
                        "name": concept_name,
                        "complexity_level": complexity
                    })
                
                analyzed_unit["topics"].append(analyzed_topic)
            
            analyzed_hierarchy["units"].append(analyzed_unit)
        
        logger.info("Successfully analyzed complexity for all concepts in hierarchy")
        return analyzed_hierarchy
        
    except Exception as e:
        logger.error(f"Error analyzing hierarchy complexity: {str(e)}", exc_info=True)
        return hierarchy
