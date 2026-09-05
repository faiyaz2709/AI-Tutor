"""
rag_service.py — Simple keyword-based RAG (Retrieval-Augmented Generation)

Flow:
  1. Take the full PDF text
  2. Split into overlapping chunks
  3. Score each chunk by keyword overlap with the student's question
  4. Return the top-N most relevant chunks joined together
"""

import re


# =========================
# CONFIGURATION
# =========================

CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 150     # overlap between consecutive chunks
TOP_N_CHUNKS = 5        # number of top chunks to include in context
MAX_CONTEXT_CHARS = 4000  # safety cap for context sent to LLM


# =========================
# TEXT CHUNKING
# =========================

def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """
    Splits a large text into overlapping chunks of fixed character size.
    Overlap ensures concepts spanning chunk boundaries are captured.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap  # move forward with overlap

    return [c for c in chunks if len(c) > 50]  # remove tiny chunks


# =========================
# KEYWORD SCORING
# =========================

def score_chunk(chunk: str, question: str) -> float:
    """
    Scores a chunk based on how many question keywords appear in it.
    Uses simple word overlap with bonus for phrase matches.
    """
    # Clean and tokenize question
    question_lower = question.lower()
    chunk_lower = chunk.lower()

    # Extract meaningful words (length > 2)
    words = re.findall(r'\b[a-z]{3,}\b', question_lower)

    # Remove common stopwords
    stopwords = {
        'the', 'and', 'for', 'are', 'was', 'what', 'how', 'why', 'when',
        'which', 'that', 'this', 'with', 'have', 'from', 'not', 'can',
        'will', 'does', 'did', 'its', 'use', 'used', 'using', 'give',
        'explain', 'define', 'tell', 'about', 'please', 'describe'
    }
    keywords = [w for w in words if w not in stopwords]

    if not keywords:
        return 0.0

    score = 0.0
    for kw in keywords:
        # Full word match
        if kw in chunk_lower:
            score += 1.0
        # Partial word match (e.g., "variable" matches "variables")
        elif any(kw in word for word in chunk_lower.split()):
            score += 0.5

    # Bonus: if question phrase appears directly
    if question_lower[:30] in chunk_lower:
        score += 2.0

    return score


# =========================
# RETRIEVE RELEVANT CONTEXT
# =========================

def get_relevant_context(pdf_text: str, question: str, top_n: int = TOP_N_CHUNKS) -> str:
    """
    Main RAG function.

    Given full PDF text and a student question:
    1. Splits PDF into chunks
    2. Scores each chunk
    3. Returns the top-N most relevant chunks joined together

    Returns a string of relevant context capped at MAX_CONTEXT_CHARS.
    """
    if not pdf_text or not question:
        return pdf_text[:MAX_CONTEXT_CHARS] if pdf_text else ""

    chunks = split_into_chunks(pdf_text)

    if not chunks:
        return pdf_text[:MAX_CONTEXT_CHARS]

    # Score all chunks
    scored = [(chunk, score_chunk(chunk, question)) for chunk in chunks]

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Take top-N chunks
    top_chunks = [chunk for chunk, score in scored[:top_n]]

    # Join and cap
    context = "\n\n---\n\n".join(top_chunks)
    context = context[:MAX_CONTEXT_CHARS]

    return context
