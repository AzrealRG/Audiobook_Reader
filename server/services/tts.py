import re
import subprocess
import time
from pathlib import Path

from google.cloud import texttospeech

from server.services.chapters import Chapter, slugify

MAX_CHUNK_BYTES = 4500
OUTPUT_DIR = Path("output")
VOICE_NAME = "en-US-Wavenet-C"
LANGUAGE_CODE = "en-US"
AUDIO_ENCODING = texttospeech.AudioEncoding.MP3
RETRY_ATTEMPTS = 3

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

def synthesize_chunk(client: texttospeech.TextToSpeechClient, text: str) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(audio_encoding=AUDIO_ENCODING)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    return response.audio_content

def _synthesize_with_retry(client: texttospeech.TextToSpeechClient, text:str) -> bytes:
    for attempt in range(RETRY_ATTEMPTS):
        try:
            return synthesize_chunk(client, text)
        except Exception:
            if attempt == RETRY_ATTEMPTS - 1:
                raise 
            time.sleep(2 ** attempt)

def synthesize_chapter(client: texttospeech.TextToSpeechClient, chapter: Chapter, out_dir = Path) -> Path:
    chunks = text_chunking(chapter.text)
    chunk_dir = out_dir / f"{chapter.index:02d}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk_paths = []
    for i, chunk in enumerate(chunks):
        chunk_path = chunk_dir / f"chunk_{i:03d}.mp3"
        if not chunk_path.exists(): # cache hit -> skip re-synthesizing (saves cost + time on reruns)
            audio = _synthesize_with_retry(client, chunk)
            chunk_path.write_bytes(audio)
        chunk_paths.append(chunk_path)
    
    output_path = out_dir / f"{chapter.index:02d}_{slugify(chapter.title)}.mp3"
    return _concatenate_mp3s(chunk_paths, output_path)

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