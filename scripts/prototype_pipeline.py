"""
Prototype pipeline: PDF -> extracted/chunked text -> TTS audio files.
 
Purpose: validate that the PDF -> TTS idea actually works and sounds good
BEFORE any FastAPI/Celery/frontend wiring exists. Everything here runs as a
single local script.
 
Setup:
  pip install PyMuPDF google-cloud-texttospeech pydub
  # pydub also needs ffmpeg installed on your system (not a pip package):
  #   macOS:   brew install ffmpeg
  #   Ubuntu:  sudo apt install ffmpeg
  #   Windows: https://ffmpeg.org/download.html
 
  Auth: create a Google Cloud service account with Text-to-Speech access,
  download its JSON key, then:
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
 
Run:
  python prototype_pipeline.py path/to/book.pdf
"""

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import fitz
from dotenv import load_dotenv
from google.cloud import texttospeech, vision

load_dotenv()

# Config — tune these while you experiment
MAX_CHUNK_BYTES = 4500
OUTPUT_DIR = Path("output")
VOICE_NAME = "en-US-Wavenet-C"
LANGUAGE_CODE = "en-US"
AUDIO_ENCODING = texttospeech.AudioEncoding.MP3
RETRY_ATTEMPTS = 3

# Base chapter splitting recognition(subject to change later)
CHAPTER_PATTERN = re.compile(
    r"^\s*(chapter|part)\s+([\divxlc]+|\w+)\s*$", re.IGNORECASE | re.MULTILINE
)

@dataclass
class Chapter:
    index: int
    title: str
    text: str

# Text Extraction

# OCR Process
MIN_CHARS_FOR_DIGITAL_TEXT = 20
OCR_RENDER_DPI = 300

_vision_client = None

def _get_vision_client():
    global _vision_client
    if _vision_client is None:
        _vision_client = vision.ImageAnnotatorClient()
    return _vision_client

def ocr_page(page: fitz.page) -> str:
    pix = page.get_pixmap(dpi=OCR_RENDER_DPI)
    image_bytes = pix.tobytes("png")

    image = vision.Image(content=image_bytes)
    response = _get_vision_client().document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Cloud Vision error: {response.error.message}")

    return response.full_text_annotation.text

# Main extractor
def extract_text_and_toc(pdf_path: str):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc() # [[level, title, page_1_indexed], ...] — [] if no bookmarks

    full_text = ""
    page_char_offsets = {} # page_num (0-indexed) -> char offset into full_text
    ocr_pages = []
    for page_num, page in enumerate(doc):
        page_char_offsets[page_num] = len(full_text)
        page_text = page.get_text()

        if len(page_text.strip()) < MIN_CHARS_FOR_DIGITAL_TEXT:
            page_text = ocr_page(page)
            ocr_pages.append(page_num)
        
        full_text = page_text
    
    doc.close()
    return full_text, toc, page_char_offsets, ocr_pages

# Clean text
def clean_text(text: str) -> str:
    text = re.sub(r"-\n", "", text) # combine hyphenated line-break words
    text = re.sub(r"-\n{2,}", "\n\n", text) # remove extra blank lines
    text = re.sub(fr"[ \t]{2,}", " ", text) # remove repeated spaces
    return text.strip()

# Heuristic splitting - Split using chapter patterns("chapter 1", "part 1", etc.)
def _split_by_heuristic(text: str) -> list[Chapter]:
    matches = list(CHAPTER_PATTERN.finditer(text))
    if not matches:
        return [Chapter(index=1, title="Full text", text = text)]
    
    chapters = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        chapters.append(Chapter(index = i + 1, title = match.group(0).strip(), text = text[start:end]))
    return chapters

# Toc splitting - Toc would hold chapters in their order if there is Toc
def _split_by_toc(text: str, toc: list, page_char_offsets: dict) -> list[Chapter]:
    top_level = [entry for entry in toc if entry[0] == 1] # ignore nested sub-sections

    if not top_level:
        return _split_by_heuristic(text)
    
    chapters = []
    for i, (_level, title, page_indexed) in enumerate(top_level):
        start = page_char_offsets.get(page_indexed - 1, 0)
        if i + 1 < len(top_level):
            next_page = top_level[i+1][2]
            end = page_char_offsets.get(next_page - 1, len(text))
        else:
            end = len(text)
        chapters.append(Chapter(index = i + 1, title = title.strip(), text = text[start:end]))
    return chapters


# Split into chapters - Main method that calls on the actuall splitter methods
def split_into_chapters(text: str, toc: list, page_char_offsets: dict) -> list[Chapter]:
    if toc:
        return _split_by_toc(text, toc, page_char_offsets)
    return _split_by_heuristic(text)

# Chunking
def text_chunking(text:str, max_bytes: int = MAX_CHUNK_BYTES) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if len(candidate.encode("utf-8")) > max_bytes:
            if current:
                chunks.append(current)
            current = sentence
        else:
            current = candidate
        
    if current:
        chunks.append(current)
    return chunks

# Synthesize chunk
def synthesize_chunk(client: texttospeech.TextToSpeechClient, text: str) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(audio_encoding=AUDIO_ENCODING)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    return response.audio_content

# Synthesize with retry
def _synthesize_with_retry(client: texttospeech.TextToSpeechClient, text:str) -> bytes:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return synthesize_chunk(client, text)
        except Exception:
            if attempt == RETRY_ATTEMPTS - 1:
                raise time.sleep(2 ** attempt)

# Synthesize chapters
def synthesize_chapter(client: texttospeech.TextToSpeechClient, chapter: Chapter, out_dir = Path) -> Path:
    chunks = text_chunking(chapter.text)
    chunk_dir = out_dir / f"{chapter.index:02d}_chunks"
    chunk_dir.mkdir(parents=True, exists_ok=True)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        chunk_path = chunk_dir / f"chunk_{i:03d}.mp3"
        if not chunk_path.exists(): # cache hit -> skip re-synthesizing (saves cost + time on reruns)
            audio = _synthesize_with_retry(client, chunk)
            chunk_path.write_bytes(audio)
        chunk_paths.append(chunk_path)
    
    output_path = out_dir / f"{chapter.index:02d}_{slugify(chapter.title)}.mp3"
    return _concatenate_mp3s(chunk_paths, output_path)

# Helper methods for Synthesize Chapter
def _concatenate_mp3s(chunk_paths: list[Path], output_path: Path) -> Path:
    list_file = output_path.parent / f"_concat_list_{output_path.stem}.txt"
    with open(list_file, "w") as f:
        for path in chunk_paths:
            f.write(f"file '{path.resolve()}'\n")

    try: 
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(output_path)
            ]
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise
    finally: 
        list_file.unlink()
    return output_path

def slugify(chapter_title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", chapter_title.lower()).strip("_")[:50] or "untitled"

# Manifest - frontends source of truth
def write_manifest(chapters: list[Chapter], out_dir: Path) -> None:
    manifest = {
        "chapters": [
            {
                "index": c.index,
                "title": c.title,
                "audio_file": f"{c.index:02d}_{slugify(c.title)}.mp3",
                "char_count": len(c.text)
            }
            for c in chapters
        ]
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

# Main function(testing stage)
def main(pdf_path: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Extracting text from {pdf_path} ...")
    text, toc, page_offsets = extract_text_and_toc(pdf_path)
    text = clean_text(text)

    chapters = split_into_chapters(text, toc, page_offsets)
    print(f"Found {len(chapters)} chapter(s).")

    client = texttospeech.TextToSpeechClient()
    for chapter in chapters:
        print(f"Synthesizing chapter {chapter.index}: {chapter.title!r} "
              f"({len(chapter.text)} chars)")
        synthesize_chapter(client, chapter, OUTPUT_DIR)
    
    write_manifest(chapters, OUTPUT_DIR)
    print(f"Done. Outputs in {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python prototype_pipeline.py path/to/book.pdf")
        sys.exit(1)
    main(sys.argv[1])