"""Floating overlay window using tkinter."""

import tkinter as tk
from enum import Enum
from typing import Optional
import threading


class AppState(Enum):
    """Application states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    FORMATTING = "formatting"
    PASTING = "pasting"
    ERROR = "error"


# State to color mapping
STATE_COLORS = {
    AppState.IDLE: "#808080",        # Gray
    AppState.RECORDING: "#FF4444",   # Red
    AppState.TRANSCRIBING: "#FFD700", # Yellow/Gold
    AppState.FORMATTING: "#FFD700",   # Yellow/Gold
    AppState.PASTING: "#44FF44",      # Green
    AppState.ERROR: "#FF8800",        # Orange
}


class OverlayWindow:
    """Floating status overlay window."""

    def __init__(
        self,
        size: int = 48,
        position: str = "bottom-right",
    ):
        self.size = size
        self.position = position
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._circle: Optional[int] = None
        self._state = AppState.IDLE
        self._ready = threading.Event()
        self._message: Optional[str] = None
        self._message_label: Optional[tk.Label] = None

    def _setup_window(self):
        """Set up the tkinter window."""
        self._root = tk.Tk()
        self._root.title("Wispr Flow")

        # Remove window decorations
        self._root.overrideredirect(True)

        # Always on top
        self._root.attributes("-topmost", True)

        # Set transparency (Windows)
        self._root.attributes("-transparentcolor", "black")

        # Set window size
        self._root.geometry(f"{self.size}x{self.size}")

        # Position window
        self._position_window()

        # Create canvas with black background (will be transparent)
        self._canvas = tk.Canvas(
            self._root,
            width=self.size,
            height=self.size,
            bg="black",
            highlightthickness=0,
        )
        self._canvas.pack()

        # Draw circle
        padding = 4
        self._circle = self._canvas.create_oval(
            padding, padding,
            self.size - padding, self.size - padding,
            fill=STATE_COLORS[AppState.IDLE],
            outline="",
        )

        # Create message label (hidden initially)
        self._message_label = tk.Label(
            self._root,
            text="",
            bg="black",
            fg="white",
            font=("Segoe UI", 9),
        )

        self._ready.set()

    def _position_window(self):
        """Position the window based on position setting."""
        if self._root is None:
            return

        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()

        margin = 20

        if self.position == "bottom-right":
            x = screen_width - self.size - margin
            y = screen_height - self.size - margin - 40  # Account for taskbar
        elif self.position == "bottom-left":
            x = margin
            y = screen_height - self.size - margin - 40
        elif self.position == "top-right":
            x = screen_width - self.size - margin
            y = margin
        elif self.position == "top-left":
            x = margin
            y = margin
        else:
            # Default to bottom-right
            x = screen_width - self.size - margin
            y = screen_height - self.size - margin - 40

        self._root.geometry(f"+{x}+{y}")

    def set_state(self, state: AppState, message: Optional[str] = None):
        """
        Update the overlay state.

        Args:
            state: New application state
            message: Optional message to display briefly
        """
        self._state = state
        self._message = message

        if self._root is not None:
            self._root.after(0, self._update_display)

    def _update_display(self):
        """Update the display (must be called from main thread)."""
        if self._canvas is None or self._circle is None:
            return

        color = STATE_COLORS.get(self._state, STATE_COLORS[AppState.IDLE])
        self._canvas.itemconfig(self._circle, fill=color)

    def show_message(self, message: str, duration_ms: int = 2000):
        """Show a temporary message near the overlay."""
        self._message = message
        if self._root is not None:
            self._root.after(0, lambda: self._display_message(duration_ms))

    def _display_message(self, duration_ms: int):
        """Display message (must be called from main thread)."""
        # This is a simplified implementation
        # In a production app, you'd create a proper tooltip window
        pass

    def run(self):
        """Run the overlay window (blocking, call from main thread)."""
        self._setup_window()
        if self._root is not None:
            self._root.mainloop()

    def start_async(self):
        """Start the overlay in a separate thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        # Wait for window to be ready
        self._ready.wait(timeout=5.0)

    def stop(self):
        """Stop the overlay window."""
        if self._root is not None:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass

    def is_ready(self) -> bool:
        """Check if the overlay is ready."""
        return self._ready.is_set()

    def update(self):
        """Process pending events (call periodically from main thread)."""
        if self._root is not None:
            try:
                self._root.update()
            except Exception:
                pass
