
"""Extract typed text from TXT, PDF, and DOCX files."""

import io
import pymupdf
from docx import Document

MAX_FILE_SIZE = 10 * 1024 * 1024


def extract_text(filename, file_bytes):
    if not file_bytes:
        raise ValueError("Uploaded file is empty")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File exceeds 10 MB limit")

    filename = filename.lower()

    if filename.endswith(".txt"):
        return file_bytes.decode("utf-8-sig")

    elif filename.endswith(".pdf"):
        with pymupdf.open(
            stream=file_bytes,
            filetype="pdf"
        ) as pdf:
            text = "\n".join(
                page.get_text() for page in pdf
            )
        return text

    elif filename.endswith(".docx"):
        document = Document(io.BytesIO(file_bytes))
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    else:
        raise ValueError(
            "Unsupported file format. "
            "Use TXT, PDF, or DOCX."
        )
