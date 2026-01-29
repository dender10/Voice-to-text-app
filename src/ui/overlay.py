"""Floating overlay window using tkinter with image-based states."""

import tkinter as tk
from enum import Enum
from typing import Optional, Dict
from pathlib import Path
from PIL import Image, ImageTk
import threading


class AppState(Enum):
    """Application states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    FORMATTING = "formatting"
    PASTING = "pasting"
    ERROR = "error"


# Tint colors per state (R, G, B, blend alpha)
STATE_TINTS = {
    AppState.RECORDING: (0, 0, 139, 120),          # Dark blue
    AppState.TRANSCRIBING: (255, 215, 0, 100),     # Yellow/Gold
    AppState.FORMATTING: (255, 215, 0, 100),       # Yellow/Gold
    AppState.PASTING: (68, 255, 68, 100),           # Green
    AppState.ERROR: (255, 136, 0, 100),             # Orange
}


class OverlayWindow:
    """Floating status overlay window."""

    def __init__(
        self,
        size: int = 48,
        position: str = "bottom-right",
    ):
        self.position = position
        self._root: Optional[tk.Tk] = None
        self._label: Optional[tk.Label] = None
        self._state = AppState.IDLE
        self._ready = threading.Event()
        self._message: Optional[str] = None
        self._message_label: Optional[tk.Label] = None

        # Image references (kept alive to prevent GC)
        self._images: Dict[AppState, ImageTk.PhotoImage] = {}
        self._pill_width = 0
        self._pill_height = 0

        # Asset paths
        self._assets_dir = Path(__file__).parent.parent.parent / "assets"

    def _load_images(self):
        """Load and prepare all state images at startup."""
        # Load the pill image (IDLE state base)
        pill_path = self._assets_dir / "preview.png"
        pill_img = Image.open(pill_path).convert("RGBA")
        self._pill_width = pill_img.width
        self._pill_height = pill_img.height

        # IDLE state: original pill
        self._images[AppState.IDLE] = ImageTk.PhotoImage(pill_img)

        # Generate tinted pill variants for all non-idle states
        for state, (r, g, b, alpha) in STATE_TINTS.items():
            tinted = self._tint_image(pill_img, r, g, b, alpha)
            self._images[state] = ImageTk.PhotoImage(tinted)

    def _tint_image(self, base: Image.Image, r: int, g: int, b: int, alpha: int) -> Image.Image:
        """Apply a color tint to an image, preserving its alpha channel."""
        # Create a solid color overlay matching base size
        overlay = Image.new("RGBA", base.size, (r, g, b, alpha))
        # Composite: blend the color overlay onto the base image
        # Use the base alpha as a mask so transparency is preserved
        result = base.copy()
        result = Image.alpha_composite(result, overlay)
        # Restore original alpha channel so transparent areas stay transparent
        result.putalpha(base.split()[3])
        return result

    def _setup_window(self):
        """Set up the tkinter window."""
        self._root = tk.Tk()
        self._root.title("Wispr Flow")

        # Load images before setting up geometry
        self._load_images()

        # Remove window decorations
        self._root.overrideredirect(True)

        # Always on top
        self._root.attributes("-topmost", True)

        # Set transparency (Windows) - black pixels become transparent
        self._root.attributes("-transparentcolor", "black")

        # Set window size to pill dimensions
        self._root.geometry(f"{self._pill_width}x{self._pill_height}")

        # Position window
        self._position_window()

        # Create label to display images, with black background (transparent)
        self._label = tk.Label(
            self._root,
            image=self._images[AppState.IDLE],
            bg="black",
            borderwidth=0,
        )
        self._label.pack(expand=True)

        self._ready.set()

    def _position_window(self):
        """Position the window based on position setting."""
        if self._root is None:
            return

        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()

        w = self._pill_width
        h = self._pill_height
        margin = 20

        # Center horizontally, sit above the taskbar
        x = (screen_width - w) // 2
        y = screen_height - h - margin - 40  # Account for taskbar

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
        if self._label is None:
            return

        image = self._images.get(self._state, self._images[AppState.IDLE])
        self._label.configure(image=image)

    def show_message(self, message: str, duration_ms: int = 2000):
        """Show a temporary message near the overlay."""
        self._message = message
        if self._root is not None:
            self._root.after(0, lambda: self._display_message(duration_ms))

    def _display_message(self, duration_ms: int):
        """Display message (must be called from main thread)."""
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
