import json
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from ..core.logger import get_logger

load_dotenv()
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
        _llm = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.5, timeout=120)
    return _llm

TASK_GENERATION_PROMPT = """
You are an experienced educational curriculum designer. Generate comprehensive, practical learning tasks for students mastering the following academic content.

CONTEXT:
Unit: {unit_name}
Topic: {topic_name}
Concepts Covered: {concepts_list}
Complexity Level: {complexity_level}

REQUIREMENTS:
1. Generate 4-6 UNIQUE learning and teaching-focused tasks that cover DIFFERENT pedagogical approaches
2. Each task MUST reinforce understanding and apply concepts in meaningful academic/real-world scenarios
3. Tasks must vary in type, difficulty, and learning objective to provide comprehensive coverage
4. Avoid duplicate task types or overlapping learning outcomes
5. Tasks should support BOTH learning (student understanding) AND teaching (educator instruction) goals
6. Create tasks that promote critical thinking, application, and mastery of ALL mentioned concepts

TASK VARIETY GUIDELINES:
- Include diverse task types: problem_solving, quiz, project, learning_activity, discussion, case_study, practical_lab
- Range difficulty: easy → easy_medium → medium → medium_hard → hard (progressive challenge)
- Cover different cognitive levels: understand, apply, analyze, synthesize, evaluate
- Combine individual work, collaborative tasks, and reflection opportunities

LEARNING GOALS:
- Knowledge retention and concept reinforcement
- Practical application in relevant scenarios
- Critical thinking and problem-solving development
- Connection between theory and practice
- Self-assessment and reflection capabilities

CONCEPT-SPECIFIC CONSIDERATION:
Generate tasks that specifically apply to these concepts: {concepts_list}
Do NOT create generic tasks. Each task should clearly target and assess mastery of the selected concepts.

TIME ESTIMATE GUIDELINES:
- easy tasks: 30-60 minutes (estimated_time_minutes)
- easy_medium tasks: 45-90 minutes
- medium tasks: 60-120 minutes  
- medium_hard tasks: 90-180 minutes
- hard tasks: 120-240 minutes (MAXIMUM 2 DAYS = 2880 minutes total)

Return ONLY a valid JSON array with NO additional text:
[
    {{
        "title": "Clear, descriptive task title",
        "description": "2-3 sentences explaining the task purpose and connection to concepts",
        "type": "problem_solving|quiz|project|learning_activity|discussion|case_study|practical_lab",
        "difficulty": "easy|easy_medium|medium|medium_hard|hard",
        "estimated_time_minutes": 45,
        "learning_objectives": ["specific_objective_1", "specific_objective_2", "specific_objective_3"],
        "concepts_addressed": ["concept_1", "concept_2"],
        "teaching_notes": "Optional guidance for educators delivering this task",
        "instructions": "Clear, sequenced instructions for task completion"
    }},
    ...
]

CRITICAL: Ensure JSON is valid and parseable. All task types must be from the allowed list. Keep time estimates reasonable and realistic.
"""

BATCH_TASK_GENERATION_PROMPT = """
You are an experienced educational curriculum designer. Generate comprehensive learning tasks for students mastering multiple concepts across topics.

CONTEXT:
Unit: {unit_name}
Topics: {topics_list}
Selected Concepts ({concept_count} total): {concepts_list}
Complexity Level: {complexity_level}

REQUIREMENTS:
1. Generate 5-8 UNIQUE tasks covering ALL selected concepts systematically
2. Distribute tasks so EACH concept is explicitly addressed in at least ONE task
3. Use DIFFERENT task types and pedagogical approaches (no duplicate patterns)
4. Tasks must prevent cheating/duplication through concept-specific questions
5. Mix individual and collaborative learning opportunities
6. Support both teaching and learning objectives
7. Progress from foundational (understanding) to advanced (analysis/synthesis)

DEDUPLICATION STRATEGY:
- Each task type should appear ONLY ONCE for this concept combination
- Vary task titles and descriptions significantly - avoid similar wording
- Different difficulty levels and cognitive demands
- Unique real-world scenarios and application contexts
- Distinct learning objectives and assessment criteria

COVERAGE MAPPING:
Ensure systematic coverage:
- Concept relationships: Which concepts connect? Create integrative tasks
- Progressive complexity: Start with individual concepts, then combinations
- Practical applications: Real-world, relevant scenarios for academic context
- Assessment types: Mix formative and summative assessment approaches

Return ONLY a valid JSON array with NO additional text:
[
    {{
        "title": "Unique task title",
        "description": "Complete description explaining which concepts it addresses",
        "type": "problem_solving|quiz|project|learning_activity|discussion|case_study|practical_lab|research|collaborative_analysis",
        "difficulty": "easy|easy_medium|medium|medium_hard|hard",
        "estimated_time_minutes": 45,
        "learning_objectives": ["objective_1", "objective_2", "objective_3"],
        "concepts_addressed": ["specific_concept_names"],
        "teaching_notes": "Guidance for educators",
        "instructions": "Clear step-by-step instructions"
    }},
    ...
]

TIME ESTIMATE GUIDELINES (Must Comply):
- easy: 30-60 minutes
- easy_medium: 45-90 minutes
- medium: 60-120 minutes
- medium_hard: 90-180 minutes
- hard: 120-240 minutes (MAXIMUM 2 DAYS = 2880 minutes limit)

CRITICAL: JSON must be valid and parseable. Keep time estimates realistic and within limits. Ensure NO duplicate tasks for this exact concept combination.
"""


def _normalize_task_for_dedup(task: dict) -> tuple:
    """
    Create a normalized signature of a task for deduplication.
    Returns a tuple of (type, main_concept, difficulty) for comparison.
    """
    task_type = task.get("type", "").lower()
    difficulty = task.get("difficulty", "").lower()
    concepts = task.get("concepts_addressed", [])
    main_concept = concepts[0] if concepts else ""
    
    return (task_type, main_concept.lower(), difficulty)


def _deduplicate_tasks(tasks: list, concepts: list) -> list:
    """
    Remove duplicate or near-duplicate tasks from a list.
    Ensures each task type appears at most once per concept combination.
    """
    if not tasks:
        return []
    
    seen_signatures = set()
    unique_tasks = []
    
    for task in tasks:
        # Create signature for deduplication
        sig = _normalize_task_for_dedup(task)
        
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            unique_tasks.append(task)
        else:
            logger.info(f"Removing duplicate task: {task.get('title', 'Unknown')} (type: {sig[0]})")
    
    return unique_tasks


def _extract_json_from_response(response: str) -> dict | list:
    """
    Extract JSON from LLM response, handling markdown code blocks.
    """
    json_str = response
    
    # Try to extract from markdown code blocks
    if "```json" in response:
        json_str = response.split("```json")[1].split("```")[0]
    elif "```" in response:
        json_str = response.split("```")[1].split("```")[0]
    
    return json.loads(json_str.strip())


def generate_tasks(
    concept_name: str,
    topic_name: str = "",
    unit_name: str = "",
    complexity: str = "MEDIUM"
) -> list:
    """
    Generate learning tasks for a single concept.
    
    Args:
        concept_name: The concept that was just learned
        topic_name: The topic containing the concept
        unit_name: The unit containing the topic
        complexity: Complexity level (LOW, MEDIUM, HIGH)
        
    Returns:
        List of task descriptions with enhanced structure and optimized effort estimates
    """
    try:
        prompt = TASK_GENERATION_PROMPT.format(
            unit_name=unit_name or "General",
            topic_name=topic_name or "General Topic",
            concepts_list=concept_name,
            complexity_level=complexity
        )
        
        llm = get_llm()
        response = llm.invoke(prompt)
        
        try:
            tasks = _extract_json_from_response(response)
            
            if isinstance(tasks, list) and len(tasks) > 0:
                # Normalize task time estimates
                from .progress_agent import _normalize_task_times
                normalized_tasks = _normalize_task_times(tasks)
                
                # Deduplicate tasks
                unique_tasks = _deduplicate_tasks(normalized_tasks, [concept_name])
                logger.info(f"Generated {len(unique_tasks)} unique tasks for concept '{concept_name}'")
                return unique_tasks
            else:
                logger.warning(f"LLM returned empty or non-list JSON for concept '{concept_name}'")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON for concept '{concept_name}': {str(e)}")
            # Return a default task structure with optimized time
            return [
                {
                    "title": f"Master {concept_name}: Comprehensive Practice",
                    "description": f"Complete integrated exercises reinforcing {concept_name} through multiple learning pathways",
                    "type": "learning_activity",
                    "difficulty": "medium",
                    "estimated_time_minutes": 105,  # Optimized time for medium difficulty
                    "learning_objectives": [
                        f"Understand core principles of {concept_name}",
                        f"Apply {concept_name} to practical scenarios",
                        f"Evaluate complex situations using {concept_name}"
                    ],
                    "concepts_addressed": [concept_name],
                    "teaching_notes": "Guide students through progressively complex problems",
                    "instructions": "Review the concept thoroughly, then complete all practice problems and reflection questions"
                }
            ]
            
    except Exception as e:
        logger.error(f"Error generating tasks for concept '{concept_name}': {str(e)}", exc_info=True)
        return []


def generate_tasks_for_concepts(
    concepts: list[dict],
    topic_name: str = "",
    unit_name: str = "",
    complexity: str = "MEDIUM"
) -> list:
    """
    Generate learning tasks for multiple selected concepts.
    Ensures comprehensive coverage with NO duplicate tasks for the same concept combination.
    Optimizes effort estimates to ensure reasonable time allocations.
    
    Args:
        concepts: List of concept dicts, each with 'name' and optionally 'complexity'
        topic_name: The topic containing the concepts
        unit_name: The unit containing the topic
        complexity: Overall complexity level (LOW, MEDIUM, HIGH)
        
    Returns:
        List of unique task descriptions covering all concepts with optimized time estimates
    """
    if not concepts:
        logger.warning("No concepts provided for task generation")
        return []
    
    try:
        # Extract concept names for the prompt
        concept_names = [c.get('name', str(c)) if isinstance(c, dict) else str(c) for c in concepts]
        concepts_str = ", ".join(concept_names)
        
        prompt = BATCH_TASK_GENERATION_PROMPT.format(
            unit_name=unit_name or "General",
            topics_list=topic_name or "General Topic",
            concepts_list=concepts_str,
            concept_count=len(concepts),
            complexity_level=complexity
        )
        
        llm = get_llm()
        response = llm.invoke(prompt)
        
        try:
            tasks = _extract_json_from_response(response)
            
            if isinstance(tasks, list) and len(tasks) > 0:
                # Normalize task time estimates
                from .progress_agent import _normalize_task_times
                normalized_tasks = _normalize_task_times(tasks)
                
                # Deduplicate tasks to prevent duplicates for this specific combination
                unique_tasks = _deduplicate_tasks(normalized_tasks, concept_names)
                logger.info(f"Generated {len(unique_tasks)} unique tasks for {len(concepts)} concepts: {concepts_str}")
                return unique_tasks
            else:
                logger.warning(f"LLM returned empty or non-list JSON for concepts: {concepts_str}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON for concepts {concepts_str}: {str(e)}")
            # Return fallback tasks with optimized times
            fallback_tasks = []
            for i, concept_name in enumerate(concept_names, 1):
                fallback_tasks.append({
                    "title": f"Task {i}: Apply {concept_name}",
                    "description": f"Apply and integrate {concept_name} with other covered concepts in practical scenarios",
                    "type": "learning_activity" if i % 2 == 0 else "problem_solving",
                    "difficulty": "medium",
                    "estimated_time_minutes": 105,  # Optimized time for medium difficulty
                    "learning_objectives": [
                        f"Master {concept_name} thoroughly",
                        "Connect concepts in integrated scenarios",
                        "Develop critical analysis skills"
                    ],
                    "concepts_addressed": [concept_name],
                    "teaching_notes": f"Focus on practical application of {concept_name}",
                    "instructions": "Analyze the provided scenario and apply your knowledge systematically"
                })
            return fallback_tasks
            
    except Exception as e:
        logger.error(f"Error generating tasks for multiple concepts: {str(e)}", exc_info=True)
        return []


def generate(concept: str, complexity: str = "MEDIUM") -> dict:
    """
    Legacy function for backward compatibility.
    Generate academic tasks based on concept complexity.
    
    Args:
        concept: Single concept name
        complexity: Complexity level (LOW, MEDIUM, HIGH)
        
    Returns:
        Dictionary with success status and generated tasks
    """
    try:
        tasks = generate_tasks(concept, complexity=complexity)
        return {
            "success": True,
            "concept": concept,
            "complexity": complexity,
            "task_count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"Error in legacy generate function: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "tasks": []
        }


def generate_batch(
    concepts: list[dict],
    topic_name: str = "",
    unit_name: str = "",
    complexity: str = "MEDIUM"
) -> dict:
    """
    Generate tasks for multiple concepts in a single batch.
    Prevents duplicate tasks for the same concept combination.
    
    Args:
        concepts: List of concept dictionaries with 'name' key
        topic_name: Topic containing these concepts
        unit_name: Unit containing the topic
        complexity: Overall complexity level
        
    Returns:
        Dictionary with success status and generated tasks
    """
    try:
        tasks = generate_tasks_for_concepts(
            concepts=concepts,
            topic_name=topic_name,
            unit_name=unit_name,
            complexity=complexity
        )
        
        concept_names = [c.get('name', str(c)) if isinstance(c, dict) else str(c) for c in concepts]
        
        return {
            "success": True,
            "concepts": concept_names,
            "concept_count": len(concepts),
            "complexity": complexity,
            "task_count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"Error in batch generate function: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "task_count": 0,
            "tasks": []
        }

