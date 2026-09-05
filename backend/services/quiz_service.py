"""
quiz_service.py — Quiz generation and management

Responsibilities:
  - Request quiz generation from LLM service
  - Validate and clean quiz response
  - Strip correct answers before sending to frontend (security)
  - Store quiz answers server-side for evaluation
"""

from services.llm_service import generate_quiz
from services.rag_service import get_relevant_context


# =========================
# QUIZ GENERATION
# =========================

def create_quiz(topic: str, level: str, pdf_text: str, question: str = "", num_questions: int = 4) -> dict:
    """
    Generates a quiz for the student.

    Args:
        topic: Selected topic (Python, DBMS, Statistics)
        level: Student level (Beginner, Intermediate, Advanced, Expert)
        pdf_text: Full PDF text for the topic
        question: Original student question (used to get relevant context)
        num_questions: Number of quiz questions to generate

    Returns:
        {
            "questions": [
                {
                    "id": 0,
                    "question": "...",
                    "options": ["A", "B", "C", "D"]
                    # correct_answer is NOT included for frontend
                }
            ],
            "total": 4
        }
    Also stores correct answers in a server-side dict for evaluation.
    """
    # Get relevant context for quiz generation
    context = get_relevant_context(pdf_text, question or topic, top_n=4)

    # Generate questions via LLM
    raw_questions = generate_quiz(
        topic=topic,
        level=level,
        context=context,
        num_questions=num_questions
    )

    # Validate and clean
    validated = _validate_questions(raw_questions)

    # Build frontend-safe questions (no correct_answer exposed)
    frontend_questions = []
    answer_key = {}

    for i, q in enumerate(validated):
        frontend_questions.append({
            "id": i,
            "question": q.get("question", f"Question {i+1}"),
            "options": q.get("options", [])
        })
        answer_key[i] = q.get("correct_answer", "")

    return {
        "questions": frontend_questions,
        "total": len(frontend_questions),
        "answer_key": answer_key  # used by backend only, never sent to frontend
    }


# =========================
# ANSWER VALIDATION
# =========================

def _validate_questions(questions: list) -> list:
    """
    Validates that each question has the required fields and correct structure.
    Filters out malformed questions.
    """
    valid = []

    for q in questions:
        if not isinstance(q, dict):
            continue

        question_text = q.get("question", "").strip()
        options = q.get("options", [])
        correct = q.get("correct_answer", "").strip()

        # Must have question text
        if not question_text:
            continue

        # Must have 2-4 options
        if not isinstance(options, list) or len(options) < 2:
            continue

        # Ensure correct_answer is one of the options
        if correct not in options:
            # If correct_answer is a letter like "A", "B", "C", "D", convert it
            letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
            if correct.upper() in letter_map:
                idx = letter_map[correct.upper()]
                if idx < len(options):
                    correct = options[idx]
            else:
                # Just take first option as default
                correct = options[0] if options else ""

        valid.append({
            "question": question_text,
            "options": options[:4],  # cap at 4 options
            "correct_answer": correct
        })

    return valid
