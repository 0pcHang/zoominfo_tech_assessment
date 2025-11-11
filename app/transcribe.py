import io
import os
import tempfile
import logging
from typing import Dict, Any, List

import whisper
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


class Transcriber:
    def __init__(self, model_name: str = "base", device: str = None):
        """
        Load the OpenAI whisper model (https://github.com/openai/whisper).
        model_name: tiny, base, small, medium, large
        device: 'cpu' or 'cuda' or None to let whisper pick (it uses torch.device)
        """
        self.model_name = model_name
        device = device or os.environ.get("WHISPER_DEVICE")
        # whisper.load_model will choose CPU if torch not configured for cuda
        logger.info("Loading whisper model=%s", model_name)
        try:
            # whisper.load_model accepts device argument like "cpu" or "cuda"
            # self.model = whisper.load_model(model_name, device=device or "cpu")
            self.model = whisper.load_model(model_name)
            self.ready = True
        except Exception:
            logger.exception("Failed to load whisper model")
            self.ready = False
            raise

    def _ensure_wav(self, data: bytes) -> str:
        """
        Convert bytes of many formats to a temporary WAV file at 16k mono.
        Returns path to the temp wav file.
        """
        try:
            audio = AudioSegment.from_file(io.BytesIO(data))
        except Exception:
            logger.exception("Unsupported or corrupt audio format")
            raise TranscriptionError("Unsupported or corrupt audio format")
        # whisper recommends 16k or 16k+; converting to 16000 Hz mono
        audio = audio.set_channels(1).set_frame_rate(16000)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(tmp.name, format="wav")
        tmp.close()
        logger.debug("Converted audio to wav: %s", tmp.name)
        return tmp.name

    def transcribe_bytes(self, data: bytes, filename: str = "") -> Dict[str, Any]:
        wav_path = self._ensure_wav(data)
        try:
            # whisper's transcribe returns dict with "text" and "segments"
            # we forward language detection and segments
            result = self.model.transcribe(wav_path, task="transcribe")
            text = result.get("text", "").strip()
            segments = result.get("segments") or []
            response = {
                "text": text,
                "language": result.get("language"),
                "segments": [
                    {"start": round(s.get("start", 0.0), 3), "end": round(s.get("end", 0.0), 3), "text": s.get("text", "").strip()}
                    for s in segments
                ],
                "model": self.model_name,
            }
            return response
        except Exception:
            logger.exception("Transcription engine error")
            raise TranscriptionError("Transcription failed")
        finally:
            try:
                os.unlink(wav_path)
            except Exception:
                pass