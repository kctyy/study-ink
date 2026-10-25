import os
import io
from PIL import Image

def extract_text_from_file(file_path):
    """Extracts text from .txt, .pdf, .png, .jpg, and .jpeg files."""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == '.pdf':
            import fitz  # PyMuPDF
            text = ""
            # Open the PDF and extract text from each page
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
            
        elif ext in ['.png', '.jpg', '.jpeg']:
            import pytesseract
            # Run Optical Character Recognition (OCR) on the image
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
            
        else:
            return f"Error: Unsupported file format {ext}"
            
    except Exception as e:
        return f"Error processing {file_path}: {e}"

# Example Usage:
if __name__ == "__main__":
    # text1 = extract_text_from_file("notes.txt")
    # text2 = extract_text_from_file("chapter1.pdf")
    # text3 = extract_text_from_file("whiteboard.png")
    pass
