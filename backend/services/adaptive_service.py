"""
adaptive_service.py — Adaptive Learning Logic

Responsibilities:
  - Determine if topic is mastered
  - Decide re-teaching strategy based on score and level
  - Return action instructions to main.py
"""

from services.evaluation_service import is_mastered
from services.llm_service import generate_reteach


# =========================
# MASTERY THRESHOLD
# =========================

MASTERY_THRESHOLD = 90.0  # percentage


# =========================
# ADAPTIVE DECISION ENGINE
# =========================

def get_adaptive_response(
    topic: str,
    level: str,
    question: str,
    material: str,
    percentage: float,
    attempt: int = 1
) -> dict:
    """
    Evaluates whether the student mastered the topic.
    If not, generates a re-teaching explanation tailored to their performance.

    Args:
        topic: Selected topic
        level: Student's learning level
        question: The original student question
        material: Relevant PDF context
        percentage: Score percentage from evaluation
        attempt: How many attempts the student has made (for tracking)

    Returns:
        {
            "mastered": bool,
            "action": "completed" | "reteach",
            "message": str,
            "reteach_explanation": str | None,
            "attempt": int
        }
    """
    mastered = is_mastered(percentage, threshold=MASTERY_THRESHOLD)

    if mastered:
        return {
            "mastered": True,
            "action": "completed",
            "message": f"🎉 Congratulations! You have mastered {topic}! Score: {percentage:.0f}%",
            "reteach_explanation": None,
            "attempt": attempt
        }
    else:
        # Generate adaptive re-teaching explanation
        reteach_explanation = generate_reteach(
            topic=topic,
            level=level,
            question=question,
            material=material,
            score_percentage=percentage
        )

        level_message = _get_level_message(level, percentage)

        return {
            "mastered": False,
            "action": "reteach",
            "message": f"📚 Score: {percentage:.0f}%. {level_message}",
            "reteach_explanation": reteach_explanation,
            "attempt": attempt
        }


# =========================
# LEVEL-SPECIFIC MESSAGES
# =========================

def _get_level_message(level: str, percentage: float) -> str:
    """
    Returns a tailored encouragement message based on level and score.
    """
    if percentage < 50:
        messages = {
            "Beginner": "No worries! Let's start from the very basics with simple examples.",
            "Intermediate": "Let's break this down more carefully with clearer examples.",
            "Advanced": "Let's identify the missing fundamentals and work through them.",
            "Expert": "Let's revisit the complex areas you may have missed."
        }
    elif percentage < 75:
        messages = {
            "Beginner": "Good effort! Let's go through this again with different examples.",
            "Intermediate": "Almost there! Let's clarify the parts you found tricky.",
            "Advanced": "Good progress! Let's dig deeper into the concepts you missed.",
            "Expert": "Good attempt! Let's focus on the technical details you may have overlooked."
        }
    else:
        messages = {
            "Beginner": "Very close! Just a few more concepts to review.",
            "Intermediate": "Great progress! Let's review the remaining concepts quickly.",
            "Advanced": "Almost mastered! Let's cover the remaining edge cases.",
            "Expert": "Nearly there! A quick review of the remaining details will help."
        }

    return messages.get(level, "Let's review this topic again to strengthen your understanding.")


# =========================
# PROGRESS TRACKING HELPER
# =========================

def get_progress_status(topics_progress: dict) -> dict:
    """
    Returns a summary of the student's overall progress.

    Args:
        topics_progress: {
            "Python": {"percentage": 80, "mastered": False, "attempts": 2},
            "DBMS": {"percentage": 95, "mastered": True, "attempts": 1},
            ...
        }

    Returns:
        {
            "total_topics": 3,
            "mastered": 1,
            "in_progress": 2,
            "overall_percentage": 58.3
        }
    """
    total = len(topics_progress)
    mastered_count = sum(1 for v in topics_progress.values() if v.get("mastered"))
    percentages = [v.get("percentage", 0) for v in topics_progress.values()]
    overall = round(sum(percentages) / total, 1) if total > 0 else 0.0

    return {
        "total_topics": total,
        "mastered": mastered_count,
        "in_progress": total - mastered_count,
        "overall_percentage": overall
    }
