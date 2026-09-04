from google.cloud import texttospeech

from server.services.ocr import extract_text_and_toc, clean_text
from server.services.tts import synthesize_chapter
from server.services.chapters import split_into_chapters, write_manifest
from server.workers.celery_app import celery_app
from server.paths import get_book_dir
from server.db import sync_session
from server.model import Book
from server.workers.celery_app import celery_app


def _update_book(book_id: str, **fields):
    with sync_session() as session:
        book = session.get(Book, book_id)
        if book is None:
            book = Book(id=book_id)
            session.add(book)
        for key, value in fields.items():
            setattr(book, key, value)
        session.commit()

@celery_app.task(bind=True)
def process_book(self, book_id:str, pdf_path: str):
    book_dir = get_book_dir(book_id)

    try:
        _update_book(book_id, "Extracting text")

        text, toc, page_offset = extract_text_and_toc(pdf_path)
        text = clean_text(text)

        _update_book(book_id, "Detecting pages")
        chapter_list = split_into_chapters(text, toc, page_offset)

        _update_book(book_id, "Generating audio", total_chapters=len(chapter_list), completed=0)
        tts_client = texttospeech.TextToSpeechClient()
        for i, chapter in enumerate(chapter_list):
            synthesize_chapter(tts_client, chapter, book_dir)
            _update_book(
                book_id, "generating_audio",
                total_chapters=len(chapter_list), completed=i + 1,
            )

        write_manifest(chapter_list, book_dir)
        _update_book(
            book_id, "ready",
            total_chapters=len(chapter_list),
        )
        return { "book_id": book_id, "status": "ready" }

    except Exception as e:
        _update_book(book_id, "failed", error=str(e))
        raise