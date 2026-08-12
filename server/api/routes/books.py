import json
import shutil
import uuid

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

from server.workers.tasks import process_book
from server.paths import get_book_dir, get_upload_path
from server.schemas import UploadResponse, StautsResponse

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

    