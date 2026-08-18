from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes import books

app = FastAPI(title="Audiobook Reader")

# Loosen for local dev with the client/ static files; tighten before deploying
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)