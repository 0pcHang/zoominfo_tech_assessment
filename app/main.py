from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from app.transcribe import Transcriber, TranscriptionError
from app.schemas import TranscriptionResponse
import logging
import os

app = FastAPI(title="Whisper Transcription Service")
logger = logging.getLogger("uvicorn.error")

MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")  # default; change via env
_transcriber = None

@app.on_event("startup")
def startup_event():
    global _transcriber
    logger.info("Starting service, loading model %s", MODEL_NAME)
    try:
        _transcriber = Transcriber(model_name=MODEL_NAME)
    except Exception as exc:
        logger.exception("Failed to initialize transcriber: %s", exc)
        # allow health to show unready; _transcriber stays None

@app.get("/health")
def health():
    ready = _transcriber is not None and _transcriber.ready
    return {"status": "ok" if ready else "starting", "model": MODEL_NAME if ready else None}

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)):
    if _transcriber is None or not _transcriber.ready:
        raise HTTPException(status_code=503, detail="Transcription model not ready")
    content_type = file.content_type or ""
    logger.info("Received file: filename=%s content_type=%s", file.filename, content_type)
    try:
        data = await file.read()
        result = _transcriber.transcribe_bytes(data, filename=file.filename)
        return JSONResponse(content=result)
    except TranscriptionError as e:
        logger.warning("Transcription error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during transcription: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")