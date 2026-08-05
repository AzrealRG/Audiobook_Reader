import argparse

from google.cloud import texttospeech

from prototype_pipeline import (
    text_chunking,
    clean_text,
    extract_text_and_toc,
    main as run_full_pipeline,
    split_into_chapters,
    synthesize_chunk,
)

#tester methods
def stage_extract(pdf_path: str) -> None:
    text, toc, _offsets = extract_text_and_toc(pdf_path)
    text = clean_text(text)

    print(f"Extracted {len(text)} characters.")
    print(f"TOC (bookmark) entries found: {len(toc)}")
    if toc:
        for entry in toc[:10]:
            print(f"  level={entry[0]} title={entry[1]!r} page={entry[2]}")
    else:
        print("  (no embedded bookmarks -> heuristic chapter detection will be used)")
 
    print("\nFirst 500 characters of cleaned text (check for garbled encoding):\n")
    print(text[:500])

def stage_chapters(pdf_path: str) -> None:
    text, toc, offsets = extract_text_and_toc(pdf_path)
    text = clean_text(text)
    chapters = split_into_chapters(text, toc, offsets)
 
    print(f"Detected {len(chapters)} chapter(s):\n")
    for c in chapters:
        print(f"  [{c.index:02d}] {c.title!r} - {len(c.text)} chars")
    print("\nSanity check: does this count/these titles match the real book's chapters?")
 
 
def stage_chunks(pdf_path: str, chapter_index: int) -> None:
    text, toc, offsets = extract_text_and_toc(pdf_path)
    text = clean_text(text)
    chapters = split_into_chapters(text, toc, offsets)
 
    chapter = next((c for c in chapters if c.index == chapter_index), None)
    if chapter is None:
        print(f"No chapter with index {chapter_index}. Available: {[c.index for c in chapters]}")
        return
 
    chunks = text_chunking(chapter.text)
    print(f"Chapter {chapter.index} ({chapter.title!r}) split into {len(chunks)} chunk(s).\n")
    for i, chunk in enumerate(chunks):
        print(f"  chunk {i}: {len(chunk.encode('utf-8'))} bytes, {len(chunk)} chars")
 
    print("\nFirst chunk preview (check it doesn't cut off mid-sentence):\n")
    print(chunks[0][:300])
 
 
def stage_synth_one(pdf_path: str, chapter_index: int) -> None:
    text, toc, offsets = extract_text_and_toc(pdf_path)
    text = clean_text(text)
    chapters = split_into_chapters(text, toc, offsets)
 
    chapter = next((c for c in chapters if c.index == chapter_index), None)
    if chapter is None:
        print(f"No chapter with index {chapter_index}. Available: {[c.index for c in chapters]}")
        return
 
    chunks = text_chunking(chapter.text)
    print(f"Synthesizing just chunk 0 of chapter {chapter_index} as a smoke test "
          f"({len(chunks)} chunks total in this chapter, only doing 1)...")
 
    client = texttospeech.TextToSpeechClient()
    audio = synthesize_chunk(client, chunks[0])
 
    out_path = "test_output.mp3"
    with open(out_path, "wb") as f:
        f.write(audio)
    print(f"Wrote {out_path} ({len(audio)} bytes). Play it and confirm the voice sounds right "
          f"and matches the text before running the full pipeline.")
 
 
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    parser.add_argument(
        "--stage",
        choices=["extract", "chapters", "chunks", "synth-one", "full"],
        required=True,
    )
    parser.add_argument("--chapter", type=int, default=1)
    args = parser.parse_args()
 
    if args.stage == "extract":
        stage_extract(args.pdf_path)
    elif args.stage == "chapters":
        stage_chapters(args.pdf_path)
    elif args.stage == "chunks":
        stage_chunks(args.pdf_path, args.chapter)
    elif args.stage == "synth-one":
        stage_synth_one(args.pdf_path, args.chapter)
    elif args.stage == "full":
        run_full_pipeline(args.pdf_path)
 
 
if __name__ == "__main__":
    main()