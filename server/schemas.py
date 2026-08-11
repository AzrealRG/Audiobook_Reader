from pydantic import BaseModel

class UploadResponse(BaseModel):
    book_id: str
    status: str

class StautsResponse(BaseModel):
    stage: str
    total_chapters: int | None = None
    completed: int | None = None
    error: str | None = None