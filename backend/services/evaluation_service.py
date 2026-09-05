"""
evaluation_service.py — Quiz answer evaluation

Responsibilities:
  - Compare student's submitted answers against the answer key
  - Calculate score, total, and percentage
  - Return structured evaluation result
"""


# =========================
# EVALUATE QUIZ ANSWERS
# =========================

def evaluate_answers(student_answers: dict, answer_key: dict) -> dict:
    """
    Evaluates student answers against the correct answer key.

    Args:
        student_answers: {question_id (int or str): selected_option (str)}
        answer_key: {question_id (int): correct_answer (str)}

    Returns:
        {
            "score": int,         # number of correct answers
            "total": int,         # total number of questions
            "percentage": float,  # score percentage
            "results": [          # per-question breakdown
                {
                    "question_id": 0,
                    "correct": True/False,
                    "selected": "...",
                    "correct_answer": "..."
                }
            ]
        }
    """
    total = len(answer_key)

    if total == 0:
        return {
            "score": 0,
            "total": 0,
            "percentage": 0.0,
            "results": []
        }

    score = 0
    results = []

    for qid, correct_answer in answer_key.items():
        # Convert qid to int if it's a string
        qid_int = int(qid) if isinstance(qid, str) else qid

        # Get student's answer (try both int and str key)
        selected = student_answers.get(qid_int) or student_answers.get(str(qid_int), "")

        is_correct = (selected.strip().lower() == correct_answer.strip().lower()) if selected else False

        if is_correct:
            score += 1

        results.append({
            "question_id": qid_int,
            "correct": is_correct,
            "selected": selected,
            "correct_answer": correct_answer
        })

    percentage = round((score / total) * 100, 1)

    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "results": results
    }


# =========================
# MASTERY CHECK
# =========================

def is_mastered(percentage: float, threshold: float = 90.0) -> bool:
    """
    Returns True if the student has mastered the topic (score >= 90%).
    """
    return percentage >= threshold
