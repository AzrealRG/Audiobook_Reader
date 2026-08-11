from pathlib import Path
from server.config import settings

def get_book_dir(book_id: str) -> Path:
    path = Path(settings.storage_path) / "audio" / book_id
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_upload_path(book_id: str, filename: str) -> Path:
    upload_dir = Path(settings.storage_path) / "uploads" / book_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / filename