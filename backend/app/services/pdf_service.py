import PyPDF2
import io
import os

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file.

    Args:
        file_path: The path to the PDF file.

    Returns:
        The extracted text content, or an error message if extraction fails.
    """
    if not os.path.exists(file_path):
        return "Error: File not found."
    if not file_path.lower().endswith(".pdf"):
        return "Error: File is not a PDF."

    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

        # Clean up text: remove extra spaces and newlines
        cleaned_text = " ".join(text.split())
        return cleaned_text
    except Exception as e:
        return f"Error extracting text: {str(e)}"
