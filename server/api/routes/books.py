import json
import shutil
import uuid

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

from server.workers.tasks import process_book
from server.paths import get_book_dir, get_upload_path
from server.schemas import UploadResponse, StatusResponse

router = APIRouter(prefix="/books", tags=["books"])

@router.post("", response_model=UploadResponse)
async def upload_book(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported right now.")
    
    book_id = str(uuid.uuid4())
    pdf_path = get_upload_path(book_id, file.filename)
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    process_book.delay(book_id, str(pdf_path))
    return UploadResponse(book_id=book_id, status="queued")

@router.get("/{book_id}", response_model=StatusResponse)
async def get_status(book_id: str):
    status_file = get_book_dir(book_id) / "status.json"
    if not status_file.exists():
        raise HTTPException(404, "Book not found")
    return json.loads(status_file.read_text())

@router.get("/{book_id}/manifest")
async def get_manifest(book_id: str):
    manifest_file = get_book_dir(book_id) / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(404, "Manifest not ready")
    return json.loads(manifest_file.reas_text())

@router.get("/{book_id}/audio/{audio_filename}")
async def get_audio(book_id: str, audio_filename: str):
    path = get_book_dir(book_id) / audio_filename
    if not path.exists():
        raise HTTPException(404, "Audio file not ready")
    return FileResponse(path, media_type="audio/mpeg")