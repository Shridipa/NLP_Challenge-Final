import json, os, uuid, re
from pypdf import PdfReader
import nltk

# Download punkt tokenizer if not already present
nltk.download("punkt")

def clean_text(text: str) -> str:
    """Remove boilerplate and normalize whitespace."""
    text = re.sub(r'HCLTech\s+Annual\s+Integrated\s+Report\s+2024–25', '', text)
    text = re.sub(r'Annual\s+Report\s+2024-25', '', text)
    text = re.sub(r'Page\s+\d+', '', text)
    text = re.sub(r'\s+', ' ', text)  # normalize spaces
    return text.strip()

def chunk_text(text, max_words=600, overlap_words=50):
    """Chunk text into sentence-aware segments."""
    sentences = nltk.sent_tokenize(text)
    chunks, current_chunk, current_len = [], [], 0

    for sent in sentences:
        words = sent.split()
        if current_len + len(words) > max_words:
            # Save current chunk
            chunks.append(" ".join(current_chunk))
            # Start new chunk with overlap
            overlap = current_chunk[-overlap_words:] if overlap_words < len(current_chunk) else current_chunk
            current_chunk = overlap + words
            current_len = len(current_chunk)
        else:
            current_chunk.extend(words)
            current_len += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def detect_section(text: str) -> str:
    """Simple heuristic: headings are short lines in all caps."""
    lines = text.split("\n")
    for line in lines:
        if line.isupper() and 3 < len(line.split()) < 10:
            return line.strip()
    return "N/A"

import pytesseract
from PIL import Image
import io

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_page_images(page):
    """Extracts text from images embedded in the PDF page using OCR."""
    text = ""
    try:
        if page.images:
            for image_file_object in page.images:
                image_data = image_file_object.data
                image = Image.open(io.BytesIO(image_data))
                text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        print(f"Warning: OCR failed for a page. Error: {e}")
    return text

def process_pdf(pdf_path, output_path):
    print(f"Reading {pdf_path} with OCR fallback...")
    reader = PdfReader(pdf_path)
    all_chunks = []
    doc_title = "HCLTech Annual Integrated Report 2024–25"
    version = "latest"

    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    for i, page in enumerate(reader.pages):
        page_number = i + 1
        if page_number % 25 == 0:
            print(f"Processing page {page_number}/{total_pages}...")

        # 1. Try standard text extraction
        text = page.extract_text()
        
        # 2. Fallback to OCR if text is missing or extremely sparse
        if not text or len(text.strip()) < 50:
            print(f"   [OCR] Converting Page {page_number} images to text...")
            ocr_text = ocr_page_images(page)
            if ocr_text.strip():
                text = ocr_text if not text else text + "\n" + ocr_text

        if not text:
            continue

        # Detect section from raw text (newlines preserved)
        section = detect_section(text) 
        
        # Then clean and chunk
        cleaned_text = clean_text(text)
        page_chunks = chunk_text(cleaned_text)

        for chunk_content in page_chunks:
            all_chunks.append({
                "doc_title": doc_title,
                "page_number": page_number,
                "section": section,
                "chunk_id": str(uuid.uuid4()),
                "version": version,
                "content": chunk_content,
                "word_count": len(chunk_content.split())
            })

    print(f"Finished processing. Total chunks: {len(all_chunks)}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)

    # Debug preview
    print("Sample chunk:", all_chunks[0])

if __name__ == "__main__":
    pdf_file = "Annual-Report-2024-25.pdf"
    output_file = "chunks.json"
    if os.path.exists(pdf_file):
        process_pdf(pdf_file, output_file)
    else:
        print(f"Error: {pdf_file} not found.")

