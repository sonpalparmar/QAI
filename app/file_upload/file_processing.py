import os
import tempfile
from fastapi import UploadFile
from PyPDF2 import PdfReader
import docx

async def process_uploaded_file(file: UploadFile) -> str:
    """Process the uploaded file and extract its content."""
    
    file_extension = file.filename.split(".")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

            if file_extension == "pdf":
                content = extract_text_from_pdf(temp_file_path)
            elif file_extension == "docx":
                content = extract_text_from_docx(temp_file_path)
            elif file_extension == "txt":
                content = extract_text_from_txt(temp_file_path)
            else:
                raise ValueError("Unsupported file type")
        except Exception as e:
            print(f"exception {str(e)}")
        # finally:
        #     os.remove(temp_file_path)

    return content

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a TXT file."""
    with open(file_path, 'r') as f:
        return f.read()
