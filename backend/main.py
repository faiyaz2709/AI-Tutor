"""
main.py — AI Tutor FastAPI Backend

Endpoints:
  GET  /            — Serve frontend web application
  GET  /health      — Health check
  GET  /topics      — List available built-in topics and uploaded documents
  POST /upload      — Upload study material (PDF, TXT, DOCX)
  GET  /uploads     — List uploaded documents
  GET  /videos      — Get personalized educational video recommendations
  POST /ask         — Get personalized AI explanation (built-in topic or uploaded file)
  POST /quiz        — Generate AI quiz questions
  POST /submit-quiz — Evaluate student quiz answers
  POST /adaptive    — Trigger adaptive re-teaching after quiz failure
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Optional, List
from pathlib import Path
import uuid

from services.pdf_service import get_pdf_text
from services.rag_service import get_relevant_context
from services.llm_service import generate_answer
from services.quiz_service import create_quiz
from services.evaluation_service import evaluate_answers
from services.adaptive_service import get_adaptive_response
from services.upload_service import (
    process_uploaded_file,
    get_uploaded_file_text,
    get_uploaded_document,
    list_uploaded_documents
)
from services.video_service import get_recommended_videos

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# =========================
# APP SETUP
# =========================

app = FastAPI(
    title="AI Tutor API",
    description="Personalized AI Tutor with adaptive learning, RAG, file upload, voice, and video support",
    version="2.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# SERVER-SIDE SESSION STORE
# =========================

quiz_sessions: Dict[str, dict] = {}


# =========================
# REQUEST MODELS
# =========================

class AskRequest(BaseModel):
    topic: str
    level: str
    question: str
    file_id: Optional[str] = None


class QuizRequest(BaseModel):
    topic: str
    level: str
    question: Optional[str] = ""
    num_questions: Optional[int] = 4
    file_id: Optional[str] = None


class SubmitQuizRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]  # {"0": "Option A", "1": "Option C", ...}


class AdaptiveRequest(BaseModel):
    topic: str
    level: str
    question: str
    percentage: float
    session_id: Optional[str] = ""
    attempt: Optional[int] = 1
    file_id: Optional[str] = None


# =========================
# ROUTES
# =========================

@app.get("/")
def home():
    """Serves the rich frontend web application."""
    index_file = FRONTEND_DIR / "index1.html"
    if not index_file.exists():
        index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "AI Tutor Backend is Running!",
        "endpoints": {
            "POST /upload": "Upload study material (PDF, TXT, DOCX)",
            "GET /uploads": "List uploaded study materials",
            "GET /videos": "Get curated educational video recommendations",
            "POST /ask": "Get personalized explanation",
            "POST /quiz": "Generate quiz questions",
            "POST /submit-quiz": "Submit and evaluate answers",
            "POST /adaptive": "Get adaptive re-teaching"
        }
    }


@app.get("/health")
@app.get("/api")
def health_check():
    """Health check endpoint returning system status and endpoint catalog."""
    return {
        "status": "healthy",
        "message": "AI Tutor Backend is Running!",
        "version": "2.0.0",
        "endpoints": {
            "POST /upload": "Upload study material (PDF, TXT, DOCX)",
            "GET /uploads": "List uploaded study materials",
            "GET /videos": "Get curated educational video recommendations",
            "POST /ask": "Get personalized explanation",
            "POST /quiz": "Generate quiz questions",
            "POST /submit-quiz": "Submit and evaluate answers",
            "POST /adaptive": "Get adaptive re-teaching"
        }
    }


@app.get("/topics")
def get_topics():
    """Returns available built-in topics and any uploaded documents."""
    default_topics = [
        {"name": "Python", "category": "Programming", "type": "builtin", "description": "Variables, OOP, control flow, functions, and core data structures"},
        {"name": "DBMS", "category": "Databases", "type": "builtin", "description": "Relational modeling, SQL queries, indexing, ACID transactions, and normalization"},
        {"name": "Statistics", "category": "Mathematics", "type": "builtin", "description": "Probability distributions, hypothesis testing, regression, and variance"}
    ]
    uploads = list_uploaded_documents()
    return {
        "default_topics": default_topics,
        "uploaded_documents": uploads
    }


# -------------------------
# FILE UPLOAD ENDPOINTS
# -------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Receives and processes an uploaded study document (PDF, TXT, DOCX).
    Extracts text, validates size/format, and registers document for RAG & Quiz.
    """
    try:
        result = await process_uploaded_file(file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload processing failed: {str(e)}")


@app.get("/uploads")
def get_uploaded_materials():
    """Returns a list of all currently active uploaded study documents."""
    return {"uploads": list_uploaded_documents()}


# -------------------------
# VIDEO RECOMMENDATIONS
# -------------------------

@app.get("/videos")
def get_videos(
    topic: str = Query(..., description="Topic name or document title"),
    level: str = Query("Beginner", description="Proficiency level (Beginner, Intermediate, Advanced, Expert)"),
    q: Optional[str] = Query(None, description="Optional specific search query")
):
    """
    Returns curated educational video learning recommendations tailored to the student's topic and level.
    """
    videos = get_recommended_videos(topic=topic, level=level, query=q)
    return {
        "topic": topic,
        "level": level,
        "videos": videos,
        "total": len(videos)
    }


# -------------------------
# POST /ask — AI Explanation
# -------------------------

@app.post("/ask")
def ask_question(data: AskRequest):
    """
    Returns a personalized AI explanation for the student's question.

    Flow:
      1. Validate inputs
      2. Load correct text (from uploaded file if file_id provided, otherwise from topic PDF)
      3. Extract relevant context using RAG
      4. Generate personalized answer using Groq LLM
      5. Return answer
    """
    # Validate inputs
    if not data.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    if not data.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not data.level.strip():
        raise HTTPException(status_code=400, detail="Level is required")

    # Load material text
    material_text = None
    if data.file_id:
        material_text = get_uploaded_file_text(data.file_id)
        if not material_text:
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded study document '{data.file_id}' not found."
            )
    else:
        material_text = get_pdf_text(data.topic)
        if material_text is None:
            raise HTTPException(
                status_code=404,
                detail=f"Study material for topic '{data.topic}' not found. Available topics: Python, DBMS, Statistics"
            )

    # RAG: Get relevant context for this question
    context = get_relevant_context(material_text, data.question)

    # Generate personalized answer
    answer = generate_answer(
        topic=data.topic,
        level=data.level,
        question=data.question,
        material=context
    )

    return {
        "answer": answer,
        "topic": data.topic,
        "level": data.level,
        "question": data.question,
        "file_id": data.file_id,
        "context_used": True  # confirms RAG context was sent
    }


# -------------------------
# POST /quiz — Generate Quiz
# -------------------------

@app.post("/quiz")
def generate_quiz_questions(data: QuizRequest):
    """
    Generates AI-powered quiz questions for the topic and level.
    Works with default topics (Python, DBMS, Statistics) or uploaded documents.
    Returns questions WITHOUT correct answers (hidden server-side).
    Returns a session_id to use when submitting answers.
    """
    if not data.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    # Load study text
    material_text = None
    if data.file_id:
        material_text = get_uploaded_file_text(data.file_id)
        if not material_text:
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded study document '{data.file_id}' not found."
            )
    else:
        material_text = get_pdf_text(data.topic)
        if material_text is None:
            raise HTTPException(
                status_code=404,
                detail=f"Study material for topic '{data.topic}' not found."
            )

    # Generate quiz
    quiz_data = create_quiz(
        topic=data.topic,
        level=data.level,
        pdf_text=material_text,
        question=data.question or data.topic,
        num_questions=data.num_questions or 4
    )

    # Store answer key with a session ID
    session_id = str(uuid.uuid4())
    quiz_sessions[session_id] = {
        "answer_key": quiz_data["answer_key"],
        "topic": data.topic,
        "level": data.level,
        "question": data.question or "",
        "file_id": data.file_id
    }

    return {
        "session_id": session_id,
        "questions": quiz_data["questions"],
        "total": quiz_data["total"],
        "topic": data.topic,
        "level": data.level,
        "file_id": data.file_id
    }


# -------------------------
# POST /submit-quiz — Evaluate
# -------------------------

@app.post("/submit-quiz")
def submit_quiz(data: SubmitQuizRequest):
    """
    Evaluates student's quiz answers against the server-side answer key.
    Returns score, percentage, per-question breakdown, and mastery status.
    """
    session = quiz_sessions.get(data.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found. Please generate a new quiz."
        )

    answer_key = session["answer_key"]

    # Evaluate answers
    evaluation = evaluate_answers(
        student_answers=data.answers,
        answer_key=answer_key
    )

    # Include session info in response
    evaluation["topic"] = session["topic"]
    evaluation["level"] = session["level"]
    evaluation["file_id"] = session.get("file_id")
    evaluation["mastered"] = evaluation["percentage"] >= 90.0

    return evaluation


# -------------------------
# POST /adaptive — Re-teach
# -------------------------

@app.post("/adaptive")
def adaptive_reteach(data: AdaptiveRequest):
    """
    Triggered when a student scores below 90%.
    Generates an adaptive re-teaching explanation using the student's study material
    (either built-in topic or uploaded file).
    """
    if not data.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    # Determine file_id if applicable
    file_id = data.file_id
    if not file_id and data.session_id and data.session_id in quiz_sessions:
        file_id = quiz_sessions[data.session_id].get("file_id")

    # Load material text for context
    material_text = None
    if file_id:
        material_text = get_uploaded_file_text(file_id)
        if not material_text:
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded study document '{file_id}' not found."
            )
    else:
        material_text = get_pdf_text(data.topic)
        if material_text is None:
            raise HTTPException(
                status_code=404,
                detail=f"Study material for topic '{data.topic}' not found."
            )

    # Get relevant context
    context = get_relevant_context(material_text, data.question or data.topic)

    # Get adaptive response
    adaptive = get_adaptive_response(
        topic=data.topic,
        level=data.level,
        question=data.question,
        material=context,
        percentage=data.percentage,
        attempt=data.attempt or 1
    )
    adaptive["file_id"] = file_id

    return adaptive