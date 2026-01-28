"""Clipboard and paste functionality."""

import time
import pyperclip
from pynput.keyboard import Controller, Key
from typing import Optional


class ClipboardOutput:
    """Handles copying to clipboard and simulating paste."""

    def __init__(self, auto_paste: bool = True, paste_delay_ms: int = 50):
        self.auto_paste = auto_paste
        self.paste_delay_ms = paste_delay_ms
        self._keyboard = Controller()

    def copy(self, text: str) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            print(f"Clipboard error: {e}")
            return False

    def paste(self) -> bool:
        """
        Simulate Ctrl+V to paste.

        Returns:
            True if paste was attempted
        """
        try:
            # Small delay before paste
            time.sleep(self.paste_delay_ms / 1000.0)

            # Simulate Ctrl+V
            self._keyboard.press(Key.ctrl)
            self._keyboard.press('v')
            self._keyboard.release('v')
            self._keyboard.release(Key.ctrl)

            return True
        except Exception as e:
            print(f"Paste error: {e}")
            return False

    def copy_and_paste(self, text: str) -> bool:
        """
        Copy text to clipboard and paste it.

        Args:
            text: Text to copy and paste

        Returns:
            True if successful
        """
        if not text:
            return False

        if not self.copy(text):
            return False

        if self.auto_paste:
            return self.paste()

        return True

    def get_clipboard(self) -> Optional[str]:
        """Get current clipboard content."""
        try:
            return pyperclip.paste()
        except Exception:
            return None
