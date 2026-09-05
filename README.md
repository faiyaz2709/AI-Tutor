# 🎓 AI Tutor — Adaptive Learning System

> An intelligent, personalized tutoring system powered by **Groq LLM**, **RAG (Retrieval-Augmented Generation)**, and a beautiful Black & Gold UI.

![Tech Stack](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![LLM](https://img.shields.io/badge/LLM-Groq-F55036?style=for-the-badge)
![Frontend](https://img.shields.io/badge/Frontend-HTML%20%2F%20CSS%20%2F%20JS-F7DF1E?style=for-the-badge&logo=javascript)
![RAG](https://img.shields.io/badge/Search-RAG%20Pipeline-6C63FF?style=for-the-badge)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **PDF / TXT / DOCX Upload** | Upload your own study materials |
| 🤖 **AI-Powered Explanations** | Context-aware answers using RAG + Groq LLM |
| 🧠 **Adaptive Learning** | Adjusts difficulty based on your performance |
| 📝 **Smart Quiz Generation** | Auto-generates MCQ quizzes from your content |
| 📊 **Performance Evaluation** | Tracks scores and provides feedback |
| 🎥 **Video Recommendations** | Curated + YouTube videos per topic |
| 🎙️ **Voice Input** | Ask questions using your microphone |
| 🔊 **AI Voice Output** | Hear the AI tutor speak answers aloud |

---

## 🏗️ Project Structure

```
AI TUTOR/
│
├── 📁 backend/                      # FastAPI Backend
│   ├── 📁 documents/                # Pre-loaded study materials
│   │   ├── Python_Notes.pdf
│   │   ├── Statistics_Notes.pdf
│   │   └── DBMS_Notes.pdf
│   │
│   ├── 📁 services/                 # Core business logic
│   │   ├── adaptive_service.py      # Adaptive difficulty engine
│   │   ├── evaluation_service.py    # Quiz scoring & feedback
│   │   ├── llm_service.py           # Groq LLM integration
│   │   ├── pdf_service.py           # PDF text extraction
│   │   ├── quiz_service.py          # Quiz generation logic
│   │   ├── rag_service.py           # RAG retrieval pipeline
│   │   ├── upload_service.py        # File upload handling
│   │   ├── video_service.py         # Video recommendations
│   │   └── __init__.py
│   │
│   ├── 📁 uploads/                  # User uploaded files (gitignored)
│   ├── main.py                      # FastAPI app & all API routes
│   ├── requirements.txt             # Python dependencies
│   └── test_all_features.py         # Full test suite
│
├── 📁 frontend/                     # Vanilla JS Frontend
│   ├── index.html                   # Login / Landing page
│   └── index1.html                  # Main app (Dashboard, Quiz, Results)
│
├── .env                             # API Keys (never commit!)
├── .gitignore
└── README.md
```

---

## 🔄 How It Works

```
User Question
     │
     ▼
RAG Pipeline (rag_service.py)
  → Chunks document text
  → Ranks chunks by keyword overlap
     │
     ▼
Groq LLM (llm_service.py)
  → Sends top chunks as context
  → Generates personalized answer
     │
     ▼
Adaptive Engine (adaptive_service.py)
  → Tracks performance history
  → Adjusts difficulty level
     │
     ▼
Response to User (Frontend)
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/YourUsername/AI-Tutor.git
cd AI-Tutor
```

### 2. Set Up the Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Add Your API Key
Create a `.env` file inside `backend/`:
```env
GROQ_API_KEY=your_groq_api_key_here
```
> Get a free API key at: https://console.groq.com

### 4. Start the Server
```bash
python -m uvicorn main:app --reload --port 8000
```

### 5. Open the App
Go to 👉 **http://localhost:8000**

---

## 🧪 Running Tests
```bash
cd backend
python test_all_features.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve frontend |
| `GET` | `/health` | Health check |
| `POST` | `/ask` | Ask a question (RAG + LLM) |
| `POST` | `/quiz` | Generate a quiz |
| `POST` | `/submit` | Submit quiz answers |
| `POST` | `/adaptive` | Get adaptive re-teaching |
| `POST` | `/upload` | Upload a document |
| `GET` | `/uploads` | List uploaded files |
| `GET` | `/videos` | Get video recommendations |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python) |
| **LLM** | Groq (LLaMA 3) |
| **RAG** | Custom keyword-based chunking |
| **PDF Parsing** | PyMuPDF / pdfplumber |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JS |
| **Voice** | Web Speech API |
| **Videos** | YouTube Data API v3 |

---

## 📸 UI Theme

The app uses a **Black & Gold** premium theme with:
- 🌑 Dark background (`#0a0a0a`)
- 🥇 Gold accents (`#d4af37`)
- ✨ Glassmorphism cards
- 💫 Smooth animations

---

## 👨‍💻 Author

Made with ❤️ for **Adaptive Learning** — helping students learn smarter, not harder.

---

## 📄 License

This project is for educational purposes.
