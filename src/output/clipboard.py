"""Clipboard and paste functionality."""

import ctypes
import time
import pyperclip
from pynput.keyboard import Controller, Key
from typing import Optional


class ClipboardOutput:
    """Handles copying to clipboard and simulating paste."""

    def __init__(self, auto_paste: bool = True, paste_delay_ms: int = 100):
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

    def _restore_focus(self, hwnd: int) -> None:
        """Restore focus to the target window before pasting.

        Windows blocks SetForegroundWindow from background processes.
        The workaround is to attach our thread's input to the foreground
        thread, make the call, then detach.
        """
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        try:
            current_hwnd = user32.GetForegroundWindow()
            if current_hwnd == hwnd:
                return  # Already focused

            target_tid = user32.GetWindowThreadProcessId(hwnd, None)
            current_tid = kernel32.GetCurrentThreadId()

            if target_tid != current_tid:
                user32.AttachThreadInput(current_tid, target_tid, True)

            # BringWindowToTop works more reliably when threads are attached
            user32.BringWindowToTop(hwnd)
            user32.ShowWindow(hwnd, 5)  # SW_SHOW
            user32.SetForegroundWindow(hwnd)

            if target_tid != current_tid:
                user32.AttachThreadInput(current_tid, target_tid, False)

            time.sleep(0.1)  # Let the OS settle after focus change
        except Exception as e:
            print(f"Focus restore warning: {e}")

    def paste(self, target_hwnd: Optional[int] = None) -> bool:
        """
        Simulate Ctrl+V to paste.

        Args:
            target_hwnd: Windows handle to restore focus to before pasting

        Returns:
            True if paste was attempted
        """
        try:
            if target_hwnd:
                self._restore_focus(target_hwnd)

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

    def copy_and_paste(self, text: str, target_hwnd: Optional[int] = None) -> bool:
        """
        Copy text to clipboard and paste it.

        Args:
            text: Text to copy and paste
            target_hwnd: Windows handle to restore focus to before pasting

        Returns:
            True if successful
        """
        if not text:
            return False

        if not self.copy(text):
            return False

        if self.auto_paste:
            return self.paste(target_hwnd=target_hwnd)

        return True

    def get_clipboard(self) -> Optional[str]:
        """Get current clipboard content."""
        try:
            return pyperclip.paste()
        except Exception:
            return None
