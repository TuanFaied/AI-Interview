from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routes import sessions, results
from .ws import router as ws_router
import os

app = FastAPI(title="AI Live Interview")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.mount("/static/tts", StaticFiles(directory="data/tts"), name="tts")

app.include_router(sessions.router)
app.include_router(results.router)
app.include_router(ws_router)

@app.get("/")
def root():
    return {"message": "AI Live Interview System"}