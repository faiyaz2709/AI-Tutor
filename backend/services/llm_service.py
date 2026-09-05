import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load .env from backend/ directory (one level up from services/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# Get API key
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing in .env file")

# Groq client
client = Groq(api_key=api_key)

# Use a valid Groq model
MODEL = "openai/gpt-oss-120b"


# =========================
# GENERATE PERSONALIZED ANSWER
# =========================

def generate_answer(topic: str, level: str, question: str, material: str) -> str:
    """
    Generates a personalized teaching response using the Groq LLM.
    Adapts explanation depth and style to the student's level.
    """

    system_prompt = f"""You are a highly personalized AI Tutor.

Your job is NOT to simply summarize the study material.
Your job is to TEACH the student personally.

The student selected:
Topic: {topic}
Learning Level: {level}

You MUST adapt your explanation to the student's selected level.

========================
LEVEL RULES
========================

BEGINNER:
- Assume the student knows almost nothing about the topic.
- Use very simple English.
- Explain difficult technical words immediately.
- Use everyday-life analogies.
- Give very easy examples.
- Do not overload the student with advanced information.

INTERMEDIATE:
- Assume the student understands the basics.
- Use moderate technical terminology.
- Explain WHY and HOW things work.
- Give practical programming or real-world examples.
- Connect the concept with related concepts.

ADVANCED:
- Assume strong technical knowledge.
- Give deep technical explanations.
- Discuss internal working, implementation details and edge cases.
- Use professional technical terminology.
- Give advanced real-world or programming examples.

EXPERT:
- Give expert-level analysis with implementation trade-offs.
- Discuss internals, optimizations, and limitations.

========================
ANSWER FORMAT
========================

Always answer in this exact structure:

1. REAL DEFINITION
Give the technically correct definition.

2. SIMPLE EXPLANATION
Explain the same concept according to the student's level.

3. WHY IS IT USED?
Explain the purpose and importance.

4. HOW IT WORKS
Explain the working step-by-step.

5. EXAMPLE
Give a concrete example appropriate for the student's level.

6. KEY POINTS
Give 3-5 important points as bullet points.

7. QUICK CHECK
Ask ONE short question to check whether the student understood.

========================
IMPORTANT RULES
========================

- Do not simply copy the PDF text.
- Do not dump large amounts of PDF text into the answer.
- Use the PDF as the primary knowledge source.
- Stay focused on the student's question.
- Do not give an expert-level explanation to a beginner.
- Do not give a beginner-level explanation to an expert.
- Make the explanation feel like a personal teacher is teaching one student.
- If the PDF does not contain enough information, clearly say so and use your general knowledge.
"""

    user_prompt = f"""The student is learning:

Topic: {topic}
Level: {level}

Student's question:
{question}

Here is the relevant study material extracted from the {topic} PDF:

{material}

Now teach this student personally based on their level: {level}.

Remember:
- Do not return raw PDF text.
- Use the material only as your knowledge source.
- Adapt your explanation style to the {level} level.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating answer: {str(e)}"


# =========================
# GENERATE QUIZ
# =========================

def generate_quiz(topic: str, level: str, context: str, num_questions: int = 4) -> list:
    """
    Generates quiz questions based on topic, level and study material.
    Returns a list of question dicts with question, options, correct_answer.
    """

    difficulty_guide = {
        "Beginner": "basic conceptual questions testing fundamental understanding",
        "Intermediate": "concept + application questions with practical scenarios",
        "Advanced": "deeper reasoning questions testing technical depth",
        "Expert": "expert-level questions on edge cases, trade-offs and implementation"
    }

    difficulty = difficulty_guide.get(level, "intermediate questions")

    system_prompt = """You are a quiz generator for an AI Tutor system.

Generate multiple choice quiz questions based on the study material.
Return ONLY a valid JSON array. No extra text before or after JSON.

Format:
[
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A"
  }
]

Rules:
- Each question must have exactly 4 options.
- correct_answer must be one of the exact option strings.
- Questions must be based on the study material provided.
- Do not repeat the same question.
- Do not include explanations outside the JSON.
"""

    user_prompt = f"""Generate {num_questions} quiz questions for:

Topic: {topic}
Level: {level}
Difficulty: {difficulty}

Study Material:
{context}

Return ONLY the JSON array, nothing else.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=1200
        )

        raw = response.choices[0].message.content.strip()

        # Try to extract JSON array even if there's surrounding text
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        questions = json.loads(raw)
        return questions

    except json.JSONDecodeError:
        # Return fallback questions if JSON parsing fails
        return _fallback_questions(topic)
    except Exception as e:
        return _fallback_questions(topic)


def _fallback_questions(topic: str) -> list:
    """Returns safe fallback questions if LLM quiz generation fails."""
    return [
        {
            "question": f"What is the main purpose of studying {topic}?",
            "options": [
                "To gain knowledge and skills",
                "To memorize without understanding",
                "To avoid practical work",
                "None of the above"
            ],
            "correct_answer": "To gain knowledge and skills"
        },
        {
            "question": f"Which best describes a key concept in {topic}?",
            "options": [
                "It is a foundational subject for computer science",
                "It is only used in mathematics",
                "It has no practical applications",
                "It is never used in real projects"
            ],
            "correct_answer": "It is a foundational subject for computer science"
        }
    ]


# =========================
# GENERATE ADAPTIVE RETEACHING
# =========================

def generate_reteach(topic: str, level: str, question: str, material: str, score_percentage: float) -> str:
    """
    Generates a re-teaching explanation when the student scores below 90%.
    Adjusts based on score and level.
    """

    if score_percentage < 50:
        approach = "very simple, from scratch with basic analogies and examples"
    elif score_percentage < 75:
        approach = "clearer with more examples and step-by-step breakdown"
    else:
        approach = "slightly different angle with additional examples"

    reteach_level_guide = {
        "Beginner": "Keep it extremely simple. Use more analogies. Avoid technical terms.",
        "Intermediate": "Break down the concept into smaller parts. Add a practical example.",
        "Advanced": "Identify the specific missing fundamentals and explain them first.",
        "Expert": "Focus on the edge cases and implementation details that were missed."
    }

    level_instruction = reteach_level_guide.get(level, "Explain more clearly with better examples.")

    system_prompt = f"""You are an adaptive AI Tutor re-teaching a student who scored {score_percentage:.0f}% on their quiz.

The student needs a DIFFERENT explanation — not the same one repeated.

Approach: {approach}

Level Instruction: {level_instruction}

Use the same answer format:
1. REAL DEFINITION
2. SIMPLE EXPLANATION (adapted to their score)
3. WHY IS IT USED?
4. HOW IT WORKS
5. EXAMPLE (new example, different from before)
6. KEY POINTS
7. QUICK CHECK
"""

    user_prompt = f"""The student previously asked about: {question}
Topic: {topic}
Level: {level}
Their quiz score: {score_percentage:.0f}%

Study Material:
{material}

Please re-teach this concept differently. Help them understand what they missed.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=1500
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating re-teaching explanation: {str(e)}"