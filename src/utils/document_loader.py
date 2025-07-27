import io
import os
import requests
from typing import List, Dict, Optional

from pypdf import PdfReader
from docx import Document
from unstructured.partition.msg import partition_msg # for .msg outlook mails
from unstructured.partition.email import partition_email # for standard format mail ex. gmail

def load_document_from_url(url : str) -> Optional[bytes]:
    """
    Downloads document content from a given url.
    returns bytes content if successful, None Otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error loading document from {url}: {e}")
        return None
    

def get_document_type(url:str) -> str:
    """
    Determines the document type(pdf, docx, email, message, unknown) from the URL extension.
    """
    lower_url = url.lower()
    if ".pdf" in lower_url:
        return "pdf"
    elif ".docx" in lower_url:
        return "docx"
    elif ".msg" in lower_url:
        return "msg"
    elif ".eml" in lower_url:
        return "eml"
    return "unknown"

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF content using pypdf
    """
    text = ""
    try:
        with io.BytesIO(pdf_content) as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from pdf: {e}")
    return text.strip()

def extract_text_from_docx(docx_content: bytes) -> str:
    """
    Extracts text from DOCX content using python-docx.
    """
    text =""
    try:
        with io.BytesIO(docx_content) as docx_file:
            document = Document(docx_file)
            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    return text.strip()

def extract_text_from_email(email_content: bytes, file_extension: str) -> str:
    """
    Extracts text from email content(MSG or EMAIL) using unstructred.
    Handles potential deading issues.
    """
    elements = []
    try:
        if file_extension == "msg":
            elements = partition_msg(file=io.BytesIO(email_content))
        elif file_extension == "eml":
            elements = partition_email(file=io.BytesIO(email_content))
        else:
            print(f"Unsupported email file extension for extraction: {file_extension}")
            return ""
        
        text = "\n\n".join([str(el) for el in elements if hasattr(el, 'text')])
        if not text:
            text = email_content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error extracting text from email ({file_extension}): {e}")
        try:
            text = email_content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            text = email_content.decode('latin-1', errors='ignore')
    return text.strip()

def extract_text_from_document(url: str) -> Optional[str]:
    """
    Loads documents from URL and extracts text based on its type.
    """
    document_content = load_document_from_url(url)
    if document_content is None:
        return None
    
    doc_type = get_document_type(url)
    text_content = ""
    if doc_type == "pdf":
        text_content = extract_text_from_pdf(document_content)
    elif doc_type == "docx":
        text_content = extract_text_from_docx(document_content)
    elif doc_type in ["msg", "eml"]:
        text_content = extract_text_from_email(document_content, doc_type)
    else:
        print(f"Unsupported document type: {doc_type} for URL: {url}")
        return None
    
    return text_content if text_content else None