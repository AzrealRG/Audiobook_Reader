import json
import shutil
import uuid

from fastapi import APIRouter, Depends, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.workers.tasks import process_book
from server.paths import get_book_dir, get_upload_path
from server.schemas import UploadResponse, BookResponse

from server.db import get_db
from server.model import Book

router = APIRouter(prefix="/books", tags=["books"])

@router.post("", response_model=UploadResponse)
async def upload_book(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported right now.")
    
    book_id = str(uuid.uuid4())
    pdf_path = get_upload_path(book_id, file.filename)
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    db.add(Book(
        id=book_id,
        original_filename=file.filename,
        stage="queued"
    ))
    await db.commit()

    process_book.delay(book_id, str(pdf_path))
    return UploadResponse(book_id=book_id, status="queued")

@router.get("", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).order_by(Book.created_at.desc()))
    return result.scalars().all()

@router.get("/{book_id}", response_model=BookResponse)
async def get_status(book_id: str, db: AsyncSession = Depends(get_db)):
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    return book

@router.get("/{book_id}/manifest")
async def get_manifest(book_id: str):
    manifest_file = get_book_dir(book_id) / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(404, "Manifest not ready")
    return json.loads(manifest_file.read_text())

@router.get("/{book_id}/audio/{audio_filename}")
async def get_audio(book_id: str, audio_filename: str):
    path = get_book_dir(book_id) / audio_filename
    if not path.exists():
        raise HTTPException(404, "Audio file not ready")
    return FileResponse(path, media_type="audio/mpeg")