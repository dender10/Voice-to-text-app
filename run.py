"""Convenience script to run Wispr Flow from project root."""

import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import WisprFlowApp


if __name__ == "__main__":
    app = WisprFlowApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
