import json
from langchain_google_genai import GoogleGenerativeAI
from app.core.logger import get_logger

logger = get_logger(__name__)

llm = GoogleGenerativeAI(model="gemini-2.5-pro")

TASK_GENERATION_PROMPT = """
Generate 3-5 practical learning tasks for a student who has just completed learning the following concept.
These tasks should reinforce understanding and apply the concept in real-world scenarios.

Unit: {unit_name}
Topic: {topic_name}
Concept: {concept_name}

Return ONLY a valid JSON array with the following structure:
[
    {{
        "title": "Task title",
        "description": "Detailed task description",
        "type": "problem_solving|reading|quiz|project|discussion|assignment",
        "difficulty": "easy|medium|hard",
        "estimated_time_minutes": 30,
        "learning_objectives": ["objective1", "objective2"],
        "instructions": "Step by step instructions"
    }},
    ...
]

Make sure the JSON is valid and can be parsed.
"""


def generate_tasks(concept_name: str, topic_name: str = "", unit_name: str = "") -> list:
    """
    Generate learning tasks for a concept.
    
    Args:
        concept_name: The concept that was just learned
        topic_name: The topic containing the concept
        unit_name: The unit containing the topic
        
    Returns:
        List of task descriptions
    """
    try:
        prompt = TASK_GENERATION_PROMPT.format(
            unit_name=unit_name or "General",
            topic_name=topic_name or "General Topic",
            concept_name=concept_name
        )
        
        response = llm.invoke(prompt)
        
        # Try to parse the JSON response
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            tasks = json.loads(json_str.strip())
            
            if isinstance(tasks, list):
                logger.info(f"Generated {len(tasks)} tasks for concept '{concept_name}'")
                return tasks
            else:
                logger.warning(f"LLM returned non-list JSON for concept '{concept_name}'")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON for concept '{concept_name}': {str(e)}")
            # Return a default task structure
            return [
                {
                    "title": f"Practice {concept_name}",
                    "description": f"Complete exercises related to {concept_name} to reinforce your understanding",
                    "type": "practice",
                    "difficulty": "medium",
                    "estimated_time_minutes": 45,
                    "learning_objectives": [f"Master {concept_name}"],
                    "instructions": "Review the concept and complete all practice problems"
                }
            ]
            
    except Exception as e:
        logger.error(f"Error generating tasks for concept '{concept_name}': {str(e)}", exc_info=True)
        return []


def generate(concept: str, complexity: str = "MEDIUM") -> dict:
    """
    Legacy function for backward compatibility.
    Generate academic tasks based on concept complexity.
    """
    try:
        tasks = generate_tasks(concept)
        return {
            "success": True,
            "concept": concept,
            "complexity": complexity,
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"Error in legacy generate function: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

