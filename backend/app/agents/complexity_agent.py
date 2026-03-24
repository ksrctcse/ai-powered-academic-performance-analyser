from langchain_google_genai import GoogleGenerativeAI
import json
import os
from app.core.logger import get_logger

logger = get_logger(__name__)

# Lazy initialization - only create LLM when needed
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
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3, timeout=30)
        logger.info("Complexity Agent LLM initialized")
    return _llm

COMPLEXITY_PROMPT = """Analyze the following concept and classify its complexity level.
You are helping categorize educational concepts by their difficulty.
Return ONLY one of: LOW, MEDIUM, HIGH

Guidelines:
- LOW: Basic, foundational, introductory concepts
- MEDIUM: Intermediate, application-based concepts  
- HIGH: Advanced, specialized, complex concepts

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
        if not concept or not concept.strip():
            logger.warning("Empty concept provided for complexity analysis")
            return "MEDIUM"
            
        llm = get_llm()
        response = llm.invoke(COMPLEXITY_PROMPT + concept.strip())
        
        # Extract first line and clean it
        complexity_text = response.strip().split('\n')[0].upper().strip()
        logger.debug(f"LLM response for '{concept}': '{complexity_text}'")
        
        # Try to match exact values
        if complexity_text in ["LOW", "MEDIUM", "HIGH"]:
            logger.info(f"Classified '{concept}' as {complexity_text}")
            return complexity_text
        
        # Semantic analysis if exact match not found
        response_lower = complexity_text.lower()
        if any(word in response_lower for word in ["low", "easy", "basic", "simple", "fundamental", "introductory"]):
            logger.info(f"Classified '{concept}' as LOW (semantic)")
            return "LOW"
        elif any(word in response_lower for word in ["high", "hard", "difficult", "advanced", "complex", "specialized"]):
            logger.info(f"Classified '{concept}' as HIGH (semantic)")
            return "HIGH"
        else:
            logger.info(f"Classified '{concept}' as MEDIUM (default semantic)")
            return "MEDIUM"
            
    except Exception as e:
        logger.error(f"Error classifying complexity for concept '{concept}': {str(e)}", exc_info=True)
        return "MEDIUM"


def analyze_hierarchy_complexity(hierarchy: dict) -> dict:
    """
    Analyze complexity for all concepts in a hierarchical structure.
    
    Args:
        hierarchy: Dictionary with structure {course_title: str, units: [{unit_name, topics: [{topic_name, concepts: []}]}]}
        
    Returns:
        Same structure with complexity_level added to each concept
    """
    if not hierarchy or "units" not in hierarchy:
        logger.warning("No hierarchy or units found in analysis")
        return hierarchy
    
    try:
        analyzed_hierarchy = {
            "course_title": hierarchy.get("course_title", ""),
            "units": []
        }
        
        total_concepts = 0
        classified_concepts = 0
        
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
                    total_concepts += 1
                    
                    if isinstance(concept, dict):
                        concept_name = concept.get("name", concept.get("concept_name", ""))
                    else:
                        concept_name = str(concept)
                    
                    if concept_name:
                        logger.info(f"Analyzing complexity for concept: {concept_name}")
                        complexity = classify(concept_name)
                        classified_concepts += 1
                    else:
                        logger.warning("Empty concept name found, using MEDIUM")
                        complexity = "MEDIUM"
                    
                    analyzed_topic["concepts"].append({
                        "name": concept_name,
                        "complexity_level": complexity
                    })
                
                analyzed_unit["topics"].append(analyzed_topic)
            
            analyzed_hierarchy["units"].append(analyzed_unit)
        
        logger.info(f"Successfully analyzed complexity for {classified_concepts}/{total_concepts} concepts in hierarchy")
        return analyzed_hierarchy
        
    except Exception as e:
        logger.error(f"Error analyzing hierarchy complexity: {str(e)}", exc_info=True)
        return hierarchy
