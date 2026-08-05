# 📚 Audiobook Reader

An AI-powered document-to-audiobook platform that turns books and other written content into structured, listenable audio while providing tools for understanding and interacting with the text.

## Overview

Audiobook Reader is a pipeline designed to transform books from PDFs or images into structured text and eventually into full audiobooks.

The system is designed to:

1. Accept a **PDF or images of book pages**
2. Extract text using **PDF parsing and OCR**
3. Clean and organize the extracted text
4. Detect and separate **chapters**
5. Split chapters into manageable text chunks
6. Generate **AI summaries**
7. Convert the text into **natural-sounding speech**
8. Allow users to **ask questions and chat with an AI about the book**

The long-term goal is to provide an all-in-one platform for **reading, listening to, understanding, and interacting with books**.

---

## Current Status

🚧 **Prototype / Active Development**

The core document-processing and text-to-speech pipeline is currently being developed and tested.

### Currently Working

* PDF text extraction
* Text cleaning
* Chapter detection and splitting
* Text chunking
* Google Cloud Text-to-Speech integration
* End-to-end prototype pipeline testing

### In Development

* Image/PDF OCR
* More reliable chapter detection
* Improved text cleaning
* AI-generated chapter summaries
* Book-level summaries
* AI book chat
* Web/mobile user interface
* User accounts and book libraries
* Audio organization and playback

---

## Planned Architecture

```text
                  ┌─────────────────────┐
                  │    User Upload      │
                  │  PDF / Book Images  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   Text Extraction   │
                  │ PDF Parser / OCR    │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Text Cleaning    │
                  │ Formatting / Noise  │
                  │      Removal        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Chapter Detection  │
                  │    & Splitting      │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Text Chunking    │
                  └──────────┬──────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌────────────┐ ┌───────────┐ ┌────────────┐
        │    TTS     │ │ Summaries │ │  AI Chat   │
        │  Pipeline  │ │           │ │  / RAG     │
        └─────┬──────┘ └───────────┘ └────────────┘
              │
              ▼
       ┌──────────────┐
       │ Audiobook /  │
       │ Audio Player │
       └──────────────┘
```
## Pipeline

### 1. Document Input

Users will eventually be able to upload:

* PDF books
* Scanned book pages
* Images containing text

The system will determine whether the document contains machine-readable text or requires OCR.

### 2. Text Extraction

For PDFs containing selectable text, the pipeline extracts the existing text.

For scanned documents or images, OCR will be used to convert the images into text.

Potential tools include:

* PyMuPDF
* pypdf
* PaddleOCR

### 3. Text Cleaning

Extracted text is processed to remove common PDF/OCR artifacts such as:

* Unnecessary line breaks
* Repeated headers and footers
* Page numbers
* Formatting artifacts
* OCR errors

### 4. Chapter Detection

The extracted text is analyzed to identify chapter boundaries.

The pipeline can use:

* PDF table-of-contents information when available
* Chapter heading patterns
* Heuristic detection when structured chapter information is unavailable

Each chapter is stored as a structured object containing information such as:

```text
Chapter
├── index
├── title
└── text
```

### 5. Text Chunking

Long chapters are divided into smaller chunks so that they can be processed efficiently by downstream AI and TTS systems.

Chunking will eventually support:

* Context-aware boundaries
* Sentence-aware splitting
* Configurable chunk sizes
* Metadata linking chunks back to chapters

### 6. Text-to-Speech

The processed chapter text is sent to a text-to-speech service to generate audiobook audio.

The current prototype uses **Google Cloud Text-to-Speech**.

The eventual system will organize the generated audio by:

```text
Book
├── Chapter 1
│   ├── Part 1
│   ├── Part 2
│   └── ...
├── Chapter 2
│   └── ...
└── ...
```

### 7. AI Summaries

The system will generate summaries at multiple levels:

* Chapter summaries
* Section summaries
* Book summaries

This will allow users to quickly review what they have read or listened to.

### 8. AI Book Chat

The long-term goal is to allow users to have a conversation with an AI about their uploaded book.

Users will be able to ask questions such as:

> "What happened in Chapter 4?"

> "Why did the main character make that decision?"

> "What are the major themes of this book?"

> "Compare the two main characters."

The book's processed chunks can be stored and retrieved through a **RAG (Retrieval-Augmented Generation)** system so that responses are grounded in the uploaded book.

---

## Technologies

### Current / Planned

| Component      | Technology                  |
| -------------- | --------------------------- |
| Language       | Python                      |
| PDF Processing | PyMuPDF / pypdf             |
| OCR            | PaddleOCR                   |
| Text Chunking  | Custom / NLP-based          |
| Text-to-Speech | Google Cloud Text-to-Speech |
| AI / LLM       | TBD                         |
| Retrieval      | Vector Database / RAG       |
| Frontend       | TBD                         |
| Backend        | TBD                         |

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AzrealRG/Audiobook_Reader
cd Audiobook_Reader
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials/gcp-tts-key.json
```

**Never commit `.env` or Google Cloud credential files to GitHub.**

A `.env.example` file should be provided as a template.

### 5. Run the Prototype

Example:

```bash
python scripts/test_pipeline.py test_pdfs/test_book.pdf --stage chapters
```

Additional pipeline stages will be documented as they are implemented.

---

## Security

Credentials and sensitive configuration should remain local.

The following files should **never be committed**:

```text
.env
credentials/
*.json
```

unless a JSON file is explicitly intended to be public and contains no secrets.

For production, Google Cloud credentials should be managed through the backend/server environment rather than distributed to users.

---

## Roadmap

### Phase 1 — Core Pipeline

* [x] PDF text extraction
* [x] Text cleaning
* [x] Chapter detection
* [x] Text chunking
* [x] Basic TTS integration
* [ ] Improve handling of difficult PDFs
* [ ] Robust OCR pipeline

### Phase 2 — AI Processing

* [ ] Chapter summaries
* [ ] Book summaries
* [ ] Embeddings
* [ ] Vector database
* [ ] RAG pipeline
* [ ] AI book chat

### Phase 3 — Application

* [ ] Web interface
* [ ] PDF/image upload
* [ ] User accounts
* [ ] Book library
* [ ] Audio playback
* [ ] Chapter navigation
* [ ] Progress tracking

### Phase 4 — Production

* [ ] Cloud deployment
* [ ] Scalable document processing
* [ ] User authentication
* [ ] Storage for books and generated audio
* [ ] Usage limits / quotas
* [ ] Monitoring and logging
* [ ] Production security

---

## Goals

The ultimate goal of Audiobook Reader is to create more than a simple PDF-to-audio converter.

It is intended to become an **interactive AI reading platform** where users can:

**Upload → Read → Listen → Summarize → Ask Questions → Understand**

all within one application.

---

## License

License information will be added as the project approaches public release.
