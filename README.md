# Whisper Transcription Service (FastAPI)

One-paragraph architecture:
This service uses FastAPI as the HTTP layer and openai-whisper (an open-source Whisper implementation) as the transcription engine. Incoming audio is normalized via pydub to WAV/16k mono, then transcribed; responses are returned as JSON with optional time-segmented text. The service runs in Docker and includes a health endpoint.

Prerequisites:
- Docker (for containerized run)
- Python 3.12 (for local run)
- ffmpeg installed (local runs and Docker image includes ffmpeg)
- A small audio file for local tests (tests/sample_audio/hello.m4a)

Local development:
1. Create a virtualenv and install:  
   python -m venv .venv  
   source .venv/bin/activate  
   pip install -r requirements.txt  

3. Start the app:  
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4. Environment variables:  
   - WHISPER_MODEL (default "base") — model size to load

Run tests:  
- Start the app
- Place a small M4A at tests/sample_audio/hello.m4a
- Run: pytest -q

Docker:
- Build: docker build -t whisper-transcriber:latest .
- Run: docker run -p 8000:8000 whisper-transcriber:latest

API usage:
- Health:
  curl http://<host>:8000/health

- Transcribe (curl example):
  curl -X POST "http://<host>:8000/transcribe" -F "file=@./tests/sample_audio/hello.wav"

Response JSON shape:
{
  "text": "transcribed text ...",
  "language": "en",
  "segments": [
    {"start": 0.0, "end": 1.23, "text": "Hello world"}
  ],
  "model": "base"
}

Deployment (manual to your Ubuntu server):
1. Copy repository to server (git clone or scp)
2. On server: ensure Docker and docker-compose installed
3. Create an env file or export WHISPER_MODEL and WHISPER_DEVICE
4. Run:
   docker-compose up -d --build
5. Verify with curl to server:8000/health and /transcribe as above

CI/CD:
- The included GitHub Actions workflow runs tests on push.
- For automated deploy to your server: add an additional workflow step using a deploy action that SSHes into the host and runs `docker-compose pull && docker-compose up -d --build`. Use GitHub Secrets to store SSH_PRIVATE_KEY and the host IP.

Notes, trade-offs, and next steps:
- Trade-offs: default uses the small (base) model which balances speed and quality.
- Next steps: live stream transcriptions, and multiple language support. Also enable CI/CD for next time (couldn't get it completed in time)

