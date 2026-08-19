from datetime import datetime

from pydantic import BaseModel, ConfigDict

class UploadResponse(BaseModel):
    book_id: str
    status: str

class StatusResponse(BaseModel):
    stage: str
    total_chapters: int | None = None
    completed: int | None = None
    error: str | None = None

class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    original_filename: str | None = None
    stage: str
    total_chapters: int | None = None
    completed_chapters: int | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime