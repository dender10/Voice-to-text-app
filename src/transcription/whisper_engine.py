"""Whisper speech-to-text engine using OpenAI API."""

import os
import io
import numpy as np
from scipy.io import wavfile
from typing import Optional


class WhisperEngine:
    """Transcribes audio using OpenAI Whisper API."""

    def __init__(self, model_name: str = "whisper-1", device: str = "auto"):
        self.model_name = model_name
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def _load_model(self):
        """No-op for API version - kept for compatibility."""
        pass

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio to text using OpenAI Whisper API.

        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text or None if failed
        """
        if audio is None or len(audio) == 0:
            return None

        if not os.environ.get("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set")
            return None

        try:
            client = self._get_client()

            # Convert float32 audio to int16 WAV format
            audio_int16 = (audio * 32767).astype(np.int16)

            # Write to in-memory WAV file
            buffer = io.BytesIO()
            wavfile.write(buffer, sample_rate, audio_int16)
            buffer.seek(0)
            buffer.name = "audio.wav"

            # Call OpenAI Whisper API with auto language detection
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=buffer,
            )

            text = transcript.text.strip()
            return text if text else None

        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def is_model_loaded(self) -> bool:
        """Check if ready (always True for API version)."""
        return bool(os.environ.get("OPENAI_API_KEY"))
