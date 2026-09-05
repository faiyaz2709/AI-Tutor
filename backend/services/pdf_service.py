from pathlib import Path
from PyPDF2 import PdfReader


# PDF folder ka path
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"


def get_pdf_for_topic(topic: str):
    """
    Selected topic ke according PDF ka path return karta hai.
    """

    pdf_files = {
        "Python": "Python_Notes.pdf",
        "Statistics": "Statistics_Notes.pdf",
        "DBMS": "DBMS_Notes.pdf"
    }

    filename = pdf_files.get(topic)

    if not filename:
        return None

    pdf_path = DOCUMENTS_DIR / filename

    if not pdf_path.exists():
        return None

    return pdf_path


def extract_text_from_pdf(pdf_path):
    """
    PDF se pura text extract karta hai.
    """

    reader = PdfReader(str(pdf_path))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def get_pdf_text(topic: str):
    """
    Topic select karne par uski PDF ka text return karta hai.
    """

    pdf_path = get_pdf_for_topic(topic)

    if not pdf_path:
        return None

    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        return None

    return text