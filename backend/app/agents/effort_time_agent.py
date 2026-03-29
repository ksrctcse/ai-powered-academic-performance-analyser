"""
Effort & Time Allocation Agent
Intelligently allocates estimated time to individual learning tasks based on complexity.
Uses langchain with Google Generative AI to distribute time proportionally.
"""

import json
from datetime import datetime, timedelta
from langchain_google_genai import GoogleGenerativeAI
from ..core.logger import get_logger

logger = get_logger(__name__)

# Time allocation rules based on complexity
COMPLEXITY_RULES = {
    "LOW": {
        "days_duration": 2,
        "max_cumulative_minutes": 90
    },
    "MEDIUM": {
        "days_duration": 4,
        "max_cumulative_minutes": 180
    },
    "HIGH": {
        "days_duration": 6,
        "max_cumulative_minutes": 270
    }
}


def calculate_effort_time(learning_tasks, overall_complexity, start_date=None):
    """
    Intelligently allocate estimated time to learning tasks based on complexity.
    
    Args:
        learning_tasks: List of {task_title, difficulty, ...}
        overall_complexity: "LOW", "MEDIUM", "HIGH"
        start_date: datetime object (defaults to now)
    
    Returns:
        {
            "updated_tasks": [...with estimated_time_minutes],
            "end_date": calculated_end_date,
            "total_minutes": sum_of_all_minutes,
            "complexity": overall_complexity
        }
    """
    try:
        if not learning_tasks:
            return {
                "updated_tasks": [],
                "end_date": None,
                "total_minutes": 0,
                "complexity": overall_complexity
            }
        
        # Get complexity rules
        rules = COMPLEXITY_RULES.get(overall_complexity.upper(), COMPLEXITY_RULES["MEDIUM"])
        max_minutes = rules["max_cumulative_minutes"]
        days_duration = rules["days_duration"]
        
        # Calculate end date
        if not start_date:
            start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_duration)
        
        # Use langchain to intelligently allocate time
        model = GoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3)
        
        # Build task summary for the model
        tasks_summary = "\n".join([
            f"- {task.get('task_title', 'Task')}: difficulty={task.get('difficulty', 'MEDIUM')}"
            for task in learning_tasks
        ])
        
        prompt = f"""You are an educational time allocation expert. Allocate effort time (in minutes) to learning tasks based on their difficulty.

Overall Complexity: {overall_complexity}
Duration: {days_duration} days
Total Available Time: {max_minutes} minutes (cumulative for ALL tasks)

Learning Tasks:
{tasks_summary}

Rules for time allocation:
1. Distribute total {max_minutes} minutes across all tasks
2. Allocate more time to DIFFICULT tasks, less to EASY tasks
3. EASY tasks should get 20% of total time
4. MEDIUM tasks should get 50% of total time  
5. DIFFICULT/HARD tasks should get 30% of total time
6. Each task must have at least 15 minutes
7. Ensure times are realistic and cumulative equals {max_minutes}

Return ONLY valid JSON with this exact structure:
{{
  "task_allocations": [
    {{"task_title": "...", "difficulty": "...", "estimated_time_minutes": N}},
    ...
  ],
  "total_minutes": N,
  "allocation_rationale": "brief explanation"
}}

Make sure the sum of all estimated_time_minutes equals {max_minutes}."""

        response = model.invoke(prompt)
        
        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON from response if wrapped in markdown
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse LLM response as JSON")
        
        # Merge allocations with original task data
        allocations_map = {
            task["task_title"]: task.get("estimated_time_minutes", 0)
            for task in result.get("task_allocations", [])
        }
        
        updated_tasks = []
        total_minutes = 0
        
        for task in learning_tasks:
            task_title = task.get("task_title", "Task")
            allocated_time = allocations_map.get(task_title, 0)
            
            # Ensure minimum time
            if allocated_time < 15:
                allocated_time = 15
            
            updated_task = task.copy()
            updated_task["estimated_time_minutes"] = allocated_time
            updated_tasks.append(updated_task)
            total_minutes += allocated_time
        
        # Adjust if total exceeds max (redistribute)
        if total_minutes > max_minutes:
            adjustment_factor = max_minutes / total_minutes
            for task in updated_tasks:
                task["estimated_time_minutes"] = round(task["estimated_time_minutes"] * adjustment_factor)
            total_minutes = max_minutes
        
        logger.info(f"Allocated {total_minutes} minutes across {len(learning_tasks)} tasks for {overall_complexity} complexity")
        
        return {
            "updated_tasks": updated_tasks,
            "end_date": end_date.isoformat(),
            "total_minutes": total_minutes,
            "complexity": overall_complexity,
            "rationale": result.get("allocation_rationale", "")
        }
        
    except Exception as e:
        logger.error(f"Error in effort time allocation: {str(e)}", exc_info=True)
        
        # Fallback to simple equal distribution
        if learning_tasks:
            rules = COMPLEXITY_RULES.get(overall_complexity.upper(), COMPLEXITY_RULES["MEDIUM"])
            max_minutes = rules["max_cumulative_minutes"]
            time_per_task = max_minutes // len(learning_tasks)
            
            for task in learning_tasks:
                task["estimated_time_minutes"] = max(time_per_task, 15)
            
            if not start_date:
                start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=rules["days_duration"])
            
            return {
                "updated_tasks": learning_tasks,
                "end_date": end_date.isoformat(),
                "total_minutes": time_per_task * len(learning_tasks),
                "complexity": overall_complexity,
                "rationale": f"Fallback distribution: {time_per_task} mins per task"
            }
        
        return {
            "updated_tasks": [],
            "end_date": None,
            "total_minutes": 0,
            "complexity": overall_complexity,
            "error": str(e)
        }


# Quick test
if __name__ == "__main__":
    test_tasks = [
        {"task_title": "Setup JDK", "difficulty": "EASY"},
        {"task_title": "Configure Maven", "difficulty": "EASY"},
        {"task_title": "Create Maven Project", "difficulty": "MEDIUM"},
        {"task_title": "Write Build Script", "difficulty": "HARD"}
    ]
    
    result = calculate_effort_time(test_tasks, "MEDIUM")
    print(json.dumps(result, indent=2))
