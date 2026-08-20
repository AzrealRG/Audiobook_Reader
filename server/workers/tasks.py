import json

from google.cloud import texttospeech

from server.services.ocr import extract_text_and_toc, clean_text
from server.services.tts import synthesize_chapter
from server.services.chapters import split_into_chapters, write_manifest
from server.workers.celery_app import celery_app
from server.paths import get_book_dir

def _write_status(book_dir, stage: str, **extra):
    status_file = book_dir / "status.json"
    status_file.write_text(json.dumps({ "stage": stage, **extra }))

@celery_app.task(bind=True)
def process_book(self, book_id:str, pdf_path: str):
    book_dir = get_book_dir(book_id)

    try:
        _write_status(book_dir, "Extracting text")

        text, toc, page_offset = extract_text_and_toc(pdf_path)
        text = clean_text(text)

        _write_status(book_dir, "Detecting pages")
        chapter_list = split_into_chapters(text, toc, page_offset)

        _write_status(book_dir, "Generating audio", total_chapters=len(chapter_list), completed=0)
        tts_client = texttospeech.TextToSpeechClient()
        for i, chapter in enumerate(chapter_list):
            synthesize_chapter(tts_client, chapter, book_dir)
            _write_status(
                book_dir, "generating_audio",
                total_chapters=len(chapter_list), completed=i + 1,
            )

        write_manifest(chapter_list, book_dir)
        _write_status(
            book_dir, "ready",
            total_chapters=len(chapter_list),
        )
        return { "book_id": book_id, "status": "ready" }

    except Exception as e:
        _write_status(book_dir, "failed", error=str(e))
        raise