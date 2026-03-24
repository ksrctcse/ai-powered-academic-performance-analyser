import json
from langchain_google_genai import GoogleGenerativeAI
from app.core.logger import get_logger
from datetime import datetime
from typing import Optional, List, Dict

logger = get_logger(__name__)

# Initialize LLM with timeout for progress evaluation
llm = GoogleGenerativeAI(model="gemini-2.5-pro", timeout=60)

PROGRESS_EVALUATION_PROMPT = """
You are an educational progress tracking specialist. Evaluate student progress across multiple learning tasks and calculate overall completion level.

CONTEXT:
Task Title: {task_title}
Total Learning Tasks: {total_tasks}
Complexity Level: {complexity_level}

LEARNING TASKS STATUS:
{tasks_status}

REQUIREMENTS:
1. Analyze the progress for each individual learning task
2. Calculate overall task completion percentage (0-100)
3. Determine the appropriate task status: PENDING, IN_PROGRESS, COMPLETED, OVERDUE
4. Consider:
   - How many tasks are completed
   - Start date vs current date (if overdue)
   - Distribution of progress across tasks
   - Complexity-weighted progress calculation

EVALUATION CRITERIA:
- PENDING: No tasks completed, no progress
- IN_PROGRESS: Some tasks completed or at least 1% and <100% overall progress
- COMPLETED: All tasks completed and 100% overall progress
- OVERDUE: Past end date and not completed

Return ONLY a valid JSON object with NO additional text:
{{
    "overall_completion_percentage": 0-100,
    "status": "PENDING|IN_PROGRESS|COMPLETED|OVERDUE",
    "tasks_completed": number of completed tasks,
    "evaluation_notes": "Brief analysis of progress",
    "recommendations": ["suggestion_1", "suggestion_2"]
}}

CRITICAL: JSON must be valid and parseable.
"""


def _normalize_task_times(generated_tasks: List[dict]) -> List[dict]:
    """
    Normalize estimated_time_minutes across tasks.
    - Maximum 2 days (2880 minutes) per task
    - Reasonable distribution based on difficulty
    - Minimum 15 minutes per task
    
    Args:
        generated_tasks: List of task dictionaries with estimated_time_minutes
        
    Returns:
        Normalized list of tasks with optimized time estimates
    """
    if not generated_tasks:
        return []
    
    difficulty_multipliers = {
        "easy": 0.3,
        "easy_medium": 0.5,
        "medium": 0.7,
        "medium_hard": 0.9,
        "hard": 1.0
    }
    
    normalized_tasks = []
    
    for task in generated_tasks:
        task_copy = task.copy()
        
        difficulty = str(task.get("difficulty", "medium")).lower()
        original_time = task.get("estimated_time_minutes", 45)
        
        # Get base time estimate based on difficulty
        multiplier = difficulty_multipliers.get(difficulty, 0.7)
        
        # Calculate optimized time (min 15 mins, max 2 days = 2880 mins)
        # Base distribution: easy=45min, easy_medium=75min, medium=105min, medium_hard=150min, hard=180min
        base_estimates = {
            "easy": 45,
            "easy_medium": 75,
            "medium": 105,
            "medium_hard": 150,
            "hard": 180
        }
        
        optimized_time = base_estimates.get(difficulty, 105)
        
        # Cap at 2 days (2880 minutes)
        optimized_time = min(optimized_time, 2880)
        optimized_time = max(optimized_time, 15)  # Minimum 15 minutes
        
        # Cap the original estimate if it's too high
        if original_time > 2880:
            logger.info(
                f"Task '{task.get('title', 'Unknown')}' estimated time "
                f"{original_time}m capped to {optimized_time}m (max 2 days)"
            )
        
        task_copy["estimated_time_minutes"] = optimized_time
        normalized_tasks.append(task_copy)
    
    return normalized_tasks


def evaluate_task_progress(
    task_title: str,
    learning_tasks_progress: List[dict],
    complexity_level: str = "MEDIUM",
    end_date: Optional[str] = None
) -> dict:
    """
    Evaluate overall task progress based on individual learning task progress.
    Uses AI agent to intelligently assess progress and provide recommendations.
    
    Args:
        task_title: The main task title
        learning_tasks_progress: List of task progress dicts with:
            - task_title
            - completion_percentage (0-100)
            - status
        complexity_level: Overall complexity (LOW, MEDIUM, HIGH)
        end_date: Task end date for overdue calculation
        
    Returns:
        Dictionary with overall_completion_percentage, status, and recommendations
    """
    try:
        if not learning_tasks_progress:
            return {
                "overall_completion_percentage": 0,
                "status": "PENDING",
                "tasks_completed": 0,
                "evaluation_notes": "No learning tasks to evaluate",
                "recommendations": ["Begin with the first learning task"]
            }
        
        # Format tasks status for prompt
        tasks_status_str = ""
        completed_count = 0
        total_progress = 0
        
        for i, task in enumerate(learning_tasks_progress, 1):
            completion = task.get("completion_percentage", 0)
            task_status = task.get("status", "PENDING")
            task_title = task.get("task_title", f"Task {i}")
            
            if completion == 100:
                completed_count += 1
            
            total_progress += completion
            
            tasks_status_str += f"  {i}. {task_title}: {completion}% complete (Status: {task_status})\n"
        
        # Calculate average progress
        avg_progress = round(total_progress / len(learning_tasks_progress))
        
        # Build prompt
        prompt = PROGRESS_EVALUATION_PROMPT.format(
            task_title=task_title,
            total_tasks=len(learning_tasks_progress),
            complexity_level=complexity_level,
            tasks_status=tasks_status_str
        )
        
        # Get AI evaluation
        response = llm.invoke(prompt)
        
        try:
            evaluation = json.loads(response)
            
            # Validate response structure
            if "overall_completion_percentage" not in evaluation:
                evaluation["overall_completion_percentage"] = avg_progress
            if "status" not in evaluation:
                if avg_progress == 100:
                    evaluation["status"] = "COMPLETED"
                elif avg_progress == 0:
                    evaluation["status"] = "PENDING"
                else:
                    evaluation["status"] = "IN_PROGRESS"
            if "tasks_completed" not in evaluation:
                evaluation["tasks_completed"] = completed_count
            
            logger.info(
                f"Progress evaluation for '{task_title}': "
                f"{evaluation['overall_completion_percentage']}% complete, "
                f"Status: {evaluation['status']}"
            )
            
            return evaluation
            
        except json.JSONDecodeError:
            # Fallback evaluation if JSON parsing fails
            logger.warning(f"Failed to parse progress evaluation response, using fallback")
            
            if avg_progress == 100:
                status = "COMPLETED"
            elif avg_progress == 0:
                status = "PENDING"
            else:
                status = "IN_PROGRESS"
            
            return {
                "overall_completion_percentage": avg_progress,
                "status": status,
                "tasks_completed": completed_count,
                "evaluation_notes": f"{completed_count} of {len(learning_tasks_progress)} learning tasks completed",
                "recommendations": [
                    "Continue with next learning task" if avg_progress < 100 else "Task mastery achieved!"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error evaluating task progress: {str(e)}", exc_info=True)
        
        # Return sensible fallback
        return {
            "overall_completion_percentage": 0,
            "status": "PENDING",
            "tasks_completed": 0,
            "evaluation_notes": "Progress evaluation temporarily unavailable",
            "recommendations": ["Try updating progress again"]
        }


def calculate_aggregate_progress(learning_task_progress_list: List[dict]) -> int:
    """
    Calculate aggregate completion percentage from list of learning task progress.
    
    Args:
        learning_task_progress_list: List of learning task progress dicts
        
    Returns:
        Aggregate completion percentage (0-100)
    """
    if not learning_task_progress_list:
        return 0
    
    total = sum(task.get("completion_percentage", 0) for task in learning_task_progress_list)
    return round(total / len(learning_task_progress_list))
