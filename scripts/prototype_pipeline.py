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
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import fitz
from google.cloud import texttospeech

# Config — tune these while you experiment
MAX_CHUNK_BYTES = 4500
OUTPUT_DIR = Path("output")
VOICE_NAME = "en-US-Wavenet-C"
LANGUAGE_CODE = "en-US"
AUDIO_ENCODING = texttospeech.AudioEncodding.MP3
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
def extract_text_and_toc(pdf_path: str):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc() # [[level, title, page_1_indexed], ...] — [] if no bookmarks

    full_text = ""
    page_char_offsets = {} # page_num (0-indexed) -> char offset into full_text
    for page_num, page in enumerate(doc):
        page_char_offsets[page_num] = len(full_text)
        full_text += page.get_text()
    
    doc.close()
    return full_text, toc, page_char_offsets

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
        end = matches[i + 1].start if i + 1 < len(matches) else len(text)
        
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
def synthesize_chunk(clien: texttospeech.TextToSpeechClient, text: str) -> bytes:
    synthesis_input = texttospeech.Synthesisinput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=VOICE_NAME)
    audio_cofig = texttospeech.AudioConfig(audio_encoding=AUDIO_ENCODING)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_cofig=audio_cofig)

    return response.audio_content