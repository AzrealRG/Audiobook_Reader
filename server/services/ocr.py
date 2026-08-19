import re

import fitz
from google.cloud import vision

MIN_CHARS_FOR_DIGITAL_TEXT = 20
OCR_RENDER_DPI = 300

_vision_client = None

def _get_vision_client():
    global _vision_client
    if _vision_client is None:
        _vision_client = vision.ImageAnnotatorClient()
    return _vision_client

def ocr_page(page: "fitz.Page") -> str:
    pix = page.get_pixmap(dpi=OCR_RENDER_DPI)
    image_bytes = pix.tobytes("png")

    image = vision.Image(content=image_bytes)
    response = _get_vision_client().document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Cloud Vision error: {response.error.message}")

    return response.full_text_annotation.text

def extract_text_and_toc(pdf_path: str):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc() # [[level, title, page_1_indexed], ...] — [] if no bookmarks

    full_text = ""
    page_char_offsets = {} # page_num (0-indexed) -> char offset into full_text
    for page_num, page in enumerate(doc):
        page_char_offsets[page_num] = len(full_text)
        page_text = page.get_text()

        if len(page_text.strip()) < MIN_CHARS_FOR_DIGITAL_TEXT:
            page_text = ocr_page(page)
        
        full_text += page_text
    
    doc.close()
    return full_text, toc, page_char_offsets

def clean_text(text: str) -> str:
    text = re.sub(r"-\n", "", text) # combine hyphenated line-break words
    text = re.sub(r"-\n{2,}", "\n\n", text) # remove extra blank lines
    text = re.sub(fr"[ \t]{2,}", " ", text) # remove repeated spaces
    return text.strip()