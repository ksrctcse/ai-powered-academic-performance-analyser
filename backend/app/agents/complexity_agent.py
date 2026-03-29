from langchain_google_genai import GoogleGenerativeAI
import json
import os
from ..core.logger import get_logger

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
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3, timeout=300)
        logger.info("Complexity Agent LLM initialized")
    return _llm

BATCH_COMPLEXITY_PROMPT = """Analyze the following educational concepts and classify each complexity level.
Return ONLY a JSON object with concept names as keys and complexity levels as values.
Complexity levels must be: LOW, MEDIUM, or HIGH

Guidelines:
- LOW: Basic, foundational, introductory concepts
- MEDIUM: Intermediate, application-based concepts  
- HIGH: Advanced, specialized, complex concepts

Concepts to analyze:
{concepts_json}

Return ONLY valid JSON, no markdown or explanation:"""


def classify_batch(concepts: list) -> dict:
    """
    Classify multiple concepts' complexity levels in a single batch.
    Much faster than classifying individually.
    
    Args:
        concepts: List of concept names to analyze
        
    Returns:
        Dictionary mapping concept names to their complexity levels
    """
    if not concepts:
        return {}
    
    # Filter out empty concepts
    valid_concepts = [c for c in concepts if c and str(c).strip()]
    if not valid_concepts:
        return {}
    
    try:
        # Format concepts for the prompt
        concepts_list = [str(c).strip() for c in valid_concepts]
        concepts_json = json.dumps(concepts_list)
        prompt = BATCH_COMPLEXITY_PROMPT.format(concepts_json=concepts_json)
        
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Try to parse the JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            response_str = response.strip()
            if response_str.startswith('{'):
                complexity_dict = json.loads(response_str)
            else:
                # Try to find JSON in the response
                start_idx = response_str.find('{')
                end_idx = response_str.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    complexity_dict = json.loads(response_str[start_idx:end_idx])
                else:
                    logger.warning(f"Could not parse complexity response: {response_str[:100]}")
                    return {c: "MEDIUM" for c in valid_concepts}
            
            # Validate and clean up the response
            result = {}
            for concept in valid_concepts:
                # Try exact match and case-insensitive match
                if concept in complexity_dict:
                    value = str(complexity_dict[concept]).upper().strip()
                else:
                    # Try to find similar key
                    found = False
                    for key in complexity_dict:
                        if key.lower() == concept.lower():
                            value = str(complexity_dict[key]).upper().strip()
                            found = True
                            break
                    if not found:
                        value = "MEDIUM"
                
                # Validate the value
                if value not in ["LOW", "MEDIUM", "HIGH"]:
                    # Try semantic classification
                    value_lower = value.lower()
                    if any(word in value_lower for word in ["low", "easy", "basic", "simple"]):
                        value = "LOW"
                    elif any(word in value_lower for word in ["high", "hard", "difficult", "advanced", "complex"]):
                        value = "HIGH"
                    else:
                        value = "MEDIUM"
                
                result[concept] = value
            
            logger.info(f"Batch classified {len(result)} concepts")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse complexity response as JSON: {str(e)}")
            return {c: "MEDIUM" for c in valid_concepts}
            
    except Exception as e:
        logger.error(f"Error in batch classification: {str(e)}", exc_info=True)
        return {c: "MEDIUM" for c in valid_concepts}


def classify(concept: str) -> str:
    """
    Classify a single concept's complexity level (fallback wrapper).
    
    Args:
        concept: The concept name/description to analyze
        
    Returns:
        A complexity level: LOW, MEDIUM, or HIGH
    """
    try:
        if not concept or not concept.strip():
            logger.warning("Empty concept provided for complexity analysis")
            return "MEDIUM"
        
        result = classify_batch([concept.strip()])
        return result.get(concept.strip(), "MEDIUM")
        
    except Exception as e:
        logger.error(f"Error classifying complexity for concept '{concept}': {str(e)}", exc_info=True)
        return "MEDIUM"


def analyze_hierarchy_complexity(hierarchy: dict) -> dict:
    """
    Analyze complexity for all concepts in a hierarchical structure using batch processing.
    This is much faster than analyzing concepts individually.
    
    Args:
        hierarchy: Dictionary with structure {course_title: str, units: [{unit_name, topics: [{topic_name, concepts: []}]}]}
        
    Returns:
        Same structure with complexity_level added to each concept
    """
    if not hierarchy or "units" not in hierarchy:
        logger.warning("No hierarchy or units found in analysis")
        return hierarchy
    
    try:
        # First pass: collect all concepts
        concepts_to_analyze = []
        concept_positions = {}  # Track where each concept is in the hierarchy
        
        for unit_idx, unit in enumerate(hierarchy.get("units", [])):
            for topic_idx, topic in enumerate(unit.get("topics", [])):
                for concept_idx, concept in enumerate(topic.get("concepts", [])):
                    if isinstance(concept, dict):
                        concept_name = concept.get("name", concept.get("concept_name", ""))
                    else:
                        concept_name = str(concept).strip() if concept else ""
                    
                    if concept_name:
                        concepts_to_analyze.append(concept_name)
                        concept_positions[concept_name] = (unit_idx, topic_idx, concept_idx)
        
        logger.info(f"Found {len(concepts_to_analyze)} concepts to analyze")
        
        # Process in batches of 10 for efficiency
        BATCH_SIZE = 10
        all_complexities = {}
        
        for i in range(0, len(concepts_to_analyze), BATCH_SIZE):
            batch = concepts_to_analyze[i:i + BATCH_SIZE]
            logger.info(f"Processing batch {i // BATCH_SIZE + 1} with {len(batch)} concepts")
            
            batch_results = classify_batch(batch)
            all_complexities.update(batch_results)
        
        # Second pass: rebuild hierarchy with complexity levels
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
                        concept_name = str(concept).strip() if concept else ""
                    
                    if concept_name:
                        complexity = all_complexities.get(concept_name, "MEDIUM")
                    else:
                        complexity = "MEDIUM"
                    
                    analyzed_topic["concepts"].append({
                        "name": concept_name,
                        "complexity_level": complexity
                    })
                
                analyzed_unit["topics"].append(analyzed_topic)
            
            analyzed_hierarchy["units"].append(analyzed_unit)
        
        logger.info(f"Successfully analyzed complexity for {len(all_complexities)} concepts")
        return analyzed_hierarchy
        
    except Exception as e:
        logger.error(f"Error analyzing hierarchy complexity: {str(e)}", exc_info=True)
        return hierarchy
