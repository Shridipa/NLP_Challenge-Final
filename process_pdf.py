import json, os, uuid, re

from pypdf import PdfReader

import nltk

import pytesseract

from PIL import Image

import io

nltk.download("punkt", quiet=True)

def clean_text(text: str) -> str:

                                                                                         

    text = re.sub(r'HCLTech\s+Annual\s+Integrated\s+Report\s+2024–25', '', text)

    text = re.sub(r'Annual\s+Report\s+2024-25', '', text)

    text = re.sub(r'P\s?a\s?g\s?e\s+\d+', '', text)

    

                                                     

    text = text.replace("/r_t.liga", "rt").replace("/r_f.liga", "rf")

    text = text.replace("t_t.liga", "tt").replace("f_f.liga", "ff")

    text = text.replace("f_i.liga", "fi").replace("f_l.liga", "fl")

    text = text.replace("/uni20B9", "₹") 

    text = text.replace("/uniF0B7", "•")                      

    

                                                         

    text = re.sub(r'\.{4,}', '...', text)

    

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

def get_bigrams(text):

                                                                  

    words = re.findall(r'\w{3,}', text.lower())

    return [" ".join(pair) for pair in zip(words, words[1:])]

def chunk_text(text, max_words=450, overlap_words=80):

                                                                                  

    sentences = nltk.sent_tokenize(text)

    chunks, current_chunk, current_len = [], [], 0

    for sent in sentences:

        words = sent.split()

        if len(words) > max_words:

            for i in range(0, len(words), max_words - overlap_words):

                chunks.append(" ".join(words[i:i + max_words]))

            continue

        if current_len + len(words) > max_words:

            if current_chunk:

                chunks.append(" ".join(current_chunk))

            overlap = current_chunk[-overlap_words:] if overlap_words < len(current_chunk) else current_chunk

            current_chunk = overlap + words

            current_len = len(current_chunk)

        else:

            current_chunk.extend(words)

            current_len += len(words)

    if current_chunk:

        chunks.append(" ".join(current_chunk))

    

    final_chunks = []

    for c in chunks:

        if len(c.split()) > 30:

            final_chunks.append({

                "content": c,

                "bigrams": get_bigrams(c)

            })

    return final_chunks

def detect_section(text: str) -> str:

                                                                       

    lines = text.split("\n")

                                           

    for line in lines[:5]:

        line = line.strip()

        if line.isupper() and 2 < len(line.split()) < 12:

            return line

            

                                                     

    text_lower = text.lower()

    if "financial highlights" in text_lower or "consolidated financial" in text_lower:

        return "Financial Statements"

    if "human resource" in text_lower or "people and culture" in text_lower or "employees" in text_lower:

        return "Human Resources"

    if "governance" in text_lower or "board of directors" in text_lower:

        return "Governance"

    if "risk management" in text_lower:

        return "Risk Management"

    if "environmental" in text_lower or "sustainability" in text_lower or "esg" in text_lower:

        return "Sustainability"

    return "N/A"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from image_classifier import classify_image

def process_page_images(page):

                                                                           

    text = ""

    image_descriptions = []

    try:

        if page.images:

            for image_file_object in page.images:

                image_data = image_file_object.data

                

                                    

                image_type = classify_image(image_data)

                image_descriptions.append(f"[Image Type: {image_type}]")

                

                     

                image = Image.open(io.BytesIO(image_data))

                ocr_text = pytesseract.image_to_string(image).strip()

                if ocr_text:

                    text += ocr_text + "\n"

    except Exception as e:

        print(f"Warning: Image processing failed. Error: {e}")

    

    return text, " ".join(image_descriptions)

def process_pdf(pdf_path, output_path):

    print(f"Processing {pdf_path}...")

    reader = PdfReader(pdf_path)

    all_chunks = []

    doc_title = "HCLTech Annual Integrated Report 2024–25"

    version = "latest"

    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):

        page_number = i + 1

        if page_number % 25 == 0:

            print(f"Page {page_number}/{total_pages}...")

        text = page.extract_text() or ""

        

                                                         

        img_text, img_descriptions = process_page_images(page)

        

                                                   

        if len(text.strip()) < 100:

            text = text + "\n" + img_text if text else img_text

        if not text and not img_descriptions:

            continue

        section = detect_section(text) 

        cleaned_text = clean_text(text)

        

                                                                                    

        if img_descriptions:

            cleaned_text = f"{img_descriptions}\n{cleaned_text}"

            

        page_chunks = chunk_text(cleaned_text)

        for chk in page_chunks:

            all_chunks.append({

                "doc_title": doc_title,

                "page_number": page_number,

                "section": section,

                "chunk_id": str(uuid.uuid4()),

                "version": version,

                "content": chk["content"],

                "bigrams": chk["bigrams"],

                "word_count": len(chk["content"].split())

            })

    with open(output_path, 'w', encoding='utf-8') as f:

        json.dump(all_chunks, f, indent=2)

    print(f"Done. Total chunks: {len(all_chunks)}")

if __name__ == "__main__":

    pdf_file = "Annual-Report-2024-25.pdf"

    output_file = "chunks.json"

    if os.path.exists(pdf_file):

        process_pdf(pdf_file, output_file)

    else:

        print(f"Error: {pdf_file} not found.")

