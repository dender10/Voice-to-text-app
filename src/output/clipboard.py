"""Clipboard and paste functionality."""

import ctypes
import logging
import time
import pyperclip
from pynput.keyboard import Controller, Key
from typing import Optional

logger = logging.getLogger(__name__)


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

    def _restore_focus(self, hwnd: int) -> bool:
        """Restore focus to the target window before pasting.

        Windows blocks SetForegroundWindow from background processes.
        The workaround is to attach our thread's input to the foreground
        thread, make the call, then detach.

        Returns:
            True if the target window has focus after the attempt.
        """
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        try:
            current_hwnd = user32.GetForegroundWindow()
            if current_hwnd == hwnd:
                logger.debug("Target window already has focus (hwnd=%s)", hwnd)
                return True

            logger.debug(
                "Restoring focus to hwnd=%s (current foreground=%s)",
                hwnd, current_hwnd,
            )

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

            # Verify focus was actually restored
            final_hwnd = user32.GetForegroundWindow()
            if final_hwnd == hwnd:
                logger.debug("Focus restored successfully to hwnd=%s", hwnd)
                return True
            else:
                logger.warning(
                    "Focus restore failed: wanted hwnd=%s but foreground is hwnd=%s",
                    hwnd, final_hwnd,
                )
                return False
        except Exception as e:
            logger.warning("Focus restore error: %s", e)
            return False

    def _send_paste_keystroke(self) -> None:
        """Send a Ctrl+V keystroke."""
        self._keyboard.press(Key.ctrl)
        self._keyboard.press('v')
        self._keyboard.release('v')
        self._keyboard.release(Key.ctrl)

    def paste(self, target_hwnd: Optional[int] = None, max_retries: int = 3) -> bool:
        """
        Simulate Ctrl+V to paste with retry logic.

        If a target window handle is provided, each attempt will try to
        restore focus before sending the keystroke.

        Args:
            target_hwnd: Windows handle to restore focus to before pasting
            max_retries: Number of attempts before giving up

        Returns:
            True if paste was attempted successfully
        """
        for attempt in range(1, max_retries + 1):
            try:
                focus_ok = True
                if target_hwnd:
                    focus_ok = self._restore_focus(target_hwnd)

                if not focus_ok and attempt < max_retries:
                    logger.info(
                        "Paste attempt %d/%d: focus not acquired, retrying in 200ms",
                        attempt, max_retries,
                    )
                    time.sleep(0.2)
                    continue

                # Small delay before paste
                time.sleep(self.paste_delay_ms / 1000.0)

                logger.info("Paste attempt %d/%d: sending Ctrl+V", attempt, max_retries)
                self._send_paste_keystroke()

                if attempt > 1:
                    logger.info("Paste succeeded on attempt %d", attempt)
                return True
            except Exception as e:
                logger.error("Paste attempt %d/%d error: %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(0.2)

        logger.error("Paste failed after %d attempts", max_retries)
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
