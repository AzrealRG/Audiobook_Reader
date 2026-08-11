import json
import re
from dataclasses import dataclass
from pathlib import Path

CHAPTER_PATTERN = re.compile(
    r"^\s*(chapter|part)\s+([\divxlc]+|\w*$)", re.IGNORECASE | re.MULTILINE
)

@dataclass
class Chapter:
    index: int
    title: str
    text: str

def _split_by_heuristic(text: str) -> list[Chapter]:
    matches = list(CHAPTER_PATTERN.finditer(text))
    if not matches:
        return [Chapter(index=1, title="Full text", text = text)]
    
    chapters = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        chapters.append(Chapter(index = i + 1, title = match.group(0).strip(), text = text[start:end]))
    return chapters

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

def split_into_chapters(text: str, toc: list, page_char_offsets: dict) -> list[Chapter]:
    if toc:
        return _split_by_toc(text, toc, page_char_offsets)
    return _split_by_heuristic(text)

def slugify(chapter_title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", chapter_title.lower()).strip("_")[:50] or "untitled"

def write_manifest(chapters: list[Chapter], out_dir: Path) -> None:
    manifest = {
        "chapters": [
            {
                "index": c.index,
                "title": c.title,
                "audio_file": f"{c.index:02d}_{slugify(c.title)}.mp3",
                "char_count": len(c.text)
            }
            for c in chapters
        ]
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))