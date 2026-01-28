"""Audio recording module using sounddevice."""

import numpy as np
import sounddevice as sd
import threading
from typing import Optional


class AudioRecorder:
    """Records audio from the microphone."""

    def __init__(self, sample_rate: int = 16000, max_seconds: int = 60):
        self.sample_rate = sample_rate
        self.max_seconds = max_seconds
        self._recording = False
        self._audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        if self._recording:
            with self._lock:
                self._audio_data.append(indata.copy())

    def start(self) -> bool:
        """Start recording audio. Returns True if started successfully."""
        try:
            with self._lock:
                self._audio_data = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback,
            )
            self._stream.start()
            return True
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self._recording = False
            return False

    def stop(self) -> Optional[np.ndarray]:
        """Stop recording and return audio data as numpy array."""
        self._recording = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                print(f"Error stopping stream: {e}")
            self._stream = None

        with self._lock:
            if not self._audio_data:
                return None

            # Concatenate all audio chunks
            audio = np.concatenate(self._audio_data, axis=0)
            self._audio_data = []

        # Flatten to 1D array
        audio = audio.flatten()

        # Enforce max duration
        max_samples = self.max_seconds * self.sample_rate
        if len(audio) > max_samples:
            audio = audio[:max_samples]

        return audio

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    @staticmethod
    def check_microphone() -> tuple[bool, str]:
        """Check if a microphone is available. Returns (success, message)."""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                return False, "No microphone found"
            default = sd.query_devices(kind='input')
            return True, f"Using: {default['name']}"
        except Exception as e:
            return False, f"Microphone error: {e}"
