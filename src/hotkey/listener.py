"""Global hotkey listener using pynput."""

from pynput import keyboard
from typing import Callable, Optional
import threading


class HotkeyListener:
    """Listens for global hotkeys (Ctrl+Shift)."""

    def __init__(
        self,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
    ):
        self.on_press = on_press
        self.on_release = on_release
        self._listener: Optional[keyboard.Listener] = None
        self._pressed_keys: set = set()
        self._hotkey_active = False
        self._lock = threading.Lock()

        # Define the hotkey combination
        self._required_keys = {
            keyboard.Key.ctrl_l,
            keyboard.Key.shift,
        }

    def _normalize_key(self, key) -> Optional[keyboard.Key]:
        """Normalize key to handle left/right variants."""
        # Handle ctrl variants
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return keyboard.Key.ctrl_l
        # Handle shift variants
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            return keyboard.Key.shift
        return key

    def _check_hotkey(self) -> bool:
        """Check if the hotkey combination is pressed."""
        normalized = {self._normalize_key(k) for k in self._pressed_keys}
        required_normalized = {self._normalize_key(k) for k in self._required_keys}
        return required_normalized.issubset(normalized)

    def _on_press(self, key):
        """Handle key press events."""
        with self._lock:
            self._pressed_keys.add(key)

            if self._check_hotkey() and not self._hotkey_active:
                self._hotkey_active = True
                if self.on_press:
                    # Run callback in separate thread to avoid blocking
                    threading.Thread(target=self.on_press, daemon=True).start()

    def _on_release(self, key):
        """Handle key release events."""
        with self._lock:
            # Check if hotkey was active and space is released
            was_active = self._hotkey_active
            normalized_key = self._normalize_key(key)

            # Discard the key from pressed set
            self._pressed_keys.discard(key)

            # Also discard normalized version for variants
            if key in (keyboard.Key.ctrl_r,):
                self._pressed_keys.discard(keyboard.Key.ctrl_l)
            if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
                self._pressed_keys.discard(keyboard.Key.shift)

            # If hotkey was active and any required key is released
            if was_active:
                if normalized_key in {keyboard.Key.ctrl_l, keyboard.Key.shift}:
                    self._hotkey_active = False
                    if self.on_release:
                        threading.Thread(target=self.on_release, daemon=True).start()

    def start(self):
        """Start listening for hotkeys."""
        if self._listener is None:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.start()

    def stop(self):
        """Stop listening for hotkeys."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._listener is not None and self._listener.running
