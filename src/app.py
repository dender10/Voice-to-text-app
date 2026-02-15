"""Main application orchestrator."""

import os
import time
import ctypes
import yaml
import threading
from pathlib import Path
from typing import Optional

from .audio.recorder import AudioRecorder
from .transcription.whisper_engine import WhisperEngine
from .formatting.gpt_formatter import GPTFormatter
from .hotkey.listener import HotkeyListener
from .ui.overlay import OverlayWindow, AppState
from .output.clipboard import ClipboardOutput


class WisprFlowApp:
    """Main application class that orchestrates all components."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._state = AppState.IDLE
        self._processing_lock = threading.Lock()

        # Initialize components
        self._init_components()

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from YAML file."""
        if config_path is None:
            # Look for config in default locations
            locations = [
                Path(__file__).parent.parent / "config" / "default_config.yaml",
                Path.cwd() / "config" / "default_config.yaml",
            ]
            for loc in locations:
                if loc.exists():
                    config_path = str(loc)
                    break

        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        # Return default config
        return {
            "audio": {"sample_rate": 16000, "max_recording_seconds": 60},
            "whisper": {"model": "base.en", "device": "auto"},
            "openai": {
                "enabled": True,
                "model": "gpt-4o-mini",
                "system_prompt": "Fix grammar and punctuation. Capitalize appropriately. Maintain meaning. Return only corrected text.",
            },
            "ui": {"overlay_position": "bottom-right", "overlay_size": 48},
            "output": {"auto_paste": True, "paste_delay_ms": 100},
        }

    def _init_components(self):
        """Initialize all components."""
        audio_cfg = self.config.get("audio", {})
        whisper_cfg = self.config.get("whisper", {})
        openai_cfg = self.config.get("openai", {})
        ui_cfg = self.config.get("ui", {})
        output_cfg = self.config.get("output", {})

        # Audio recorder
        self.recorder = AudioRecorder(
            sample_rate=audio_cfg.get("sample_rate", 16000),
            max_seconds=audio_cfg.get("max_recording_seconds", 60),
        )

        # Whisper engine
        self.whisper = WhisperEngine(
            model_name=whisper_cfg.get("model", "base.en"),
            device=whisper_cfg.get("device", "auto"),
        )

        # GPT formatter
        self.formatter = GPTFormatter(
            enabled=openai_cfg.get("enabled", True),
            model=openai_cfg.get("model", "gpt-4o-mini"),
            system_prompt=openai_cfg.get("system_prompt"),
        )

        # UI overlay
        self.overlay = OverlayWindow(
            size=ui_cfg.get("overlay_size", 48),
            position=ui_cfg.get("overlay_position", "bottom-right"),
        )

        # Clipboard output
        self.clipboard = ClipboardOutput(
            auto_paste=output_cfg.get("auto_paste", True),
            paste_delay_ms=output_cfg.get("paste_delay_ms", 100),
        )

        # Hotkey listener
        self.hotkey = HotkeyListener(
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release,
        )

    def _set_state(self, state: AppState, message: Optional[str] = None):
        """Update application state."""
        self._state = state
        self.overlay.set_state(state, message)
        print(f"State: {state.value}" + (f" - {message}" if message else ""))

    def _on_hotkey_press(self):
        """Handle hotkey press - start recording."""
        if self._state != AppState.IDLE:
            return

        with self._processing_lock:
            if self._state != AppState.IDLE:
                return

            # Capture the foreground window so we can restore focus before pasting
            self._target_hwnd = ctypes.windll.user32.GetForegroundWindow()

            self._set_state(AppState.RECORDING)
            success = self.recorder.start()

            if not success:
                self._set_state(AppState.ERROR, "Microphone error")
                # Reset to idle after delay
                threading.Timer(2.0, lambda: self._set_state(AppState.IDLE)).start()

    def _on_hotkey_release(self):
        """Handle hotkey release - stop recording and process."""
        if self._state != AppState.RECORDING:
            return

        # Process in background thread
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        """Process the recorded audio."""
        with self._processing_lock:
            # Stop recording and get audio
            audio = self.recorder.stop()

            if audio is None or len(audio) < 1600:  # Less than 0.1 seconds
                self._set_state(AppState.ERROR, "No speech detected")
                threading.Timer(1.5, lambda: self._set_state(AppState.IDLE)).start()
                return

            # Transcribe
            self._set_state(AppState.TRANSCRIBING)
            text = self.whisper.transcribe(audio, self.config["audio"]["sample_rate"])

            if not text:
                self._set_state(AppState.ERROR, "No speech detected")
                threading.Timer(1.5, lambda: self._set_state(AppState.IDLE)).start()
                return

            print(f"Transcribed: {text}")

            # Format with GPT
            if self.formatter.is_available():
                self._set_state(AppState.FORMATTING)
                formatted = self.formatter.format(text)
            else:
                formatted = text

            print(f"Formatted: {formatted}")

            # Paste — reset hotkey state first so simulated Ctrl+V
            # doesn't re-trigger the hotkey via stale modifier keys
            self._set_state(AppState.PASTING)
            self.hotkey.reset()
            success = self.clipboard.copy_and_paste(formatted, target_hwnd=self._target_hwnd)

            if success:
                time.sleep(0.15)  # let simulated key events drain
                self._set_state(AppState.IDLE)
            else:
                self._set_state(AppState.ERROR, "Paste failed")
                threading.Timer(1.5, lambda: self._set_state(AppState.IDLE)).start()

    def run(self):
        """Run the application."""
        print("Wispr Flow starting...")

        # Check microphone
        mic_ok, mic_msg = AudioRecorder.check_microphone()
        if not mic_ok:
            print(f"Error: {mic_msg}")
            return

        print(f"Microphone: {mic_msg}")

        # Check OpenAI API
        if self.whisper.is_model_loaded():
            print("Whisper API: enabled")
        else:
            print("Whisper API: disabled (no API key)")

        if self.formatter.is_available():
            print("GPT formatting: enabled")
        else:
            print("GPT formatting: disabled (no API key)")

        # Start hotkey listener
        self.hotkey.start()
        print("Hotkey listener started (Ctrl+Shift)")

        # Run overlay (blocks main thread)
        print("Starting overlay...")
        print("\nReady! Hold Ctrl+Shift to record, release to transcribe.")
        print("Press Ctrl+C to exit.\n")

        try:
            self.overlay.run()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the application."""
        print("\nShutting down...")
        self.hotkey.stop()
        self.overlay.stop()
        print("Goodbye!")
