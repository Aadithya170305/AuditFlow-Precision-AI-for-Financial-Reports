import fitz
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text
def chunk_text(text, size=500):
    return [text[i:i+size] for i in range(0, len(text), size)]