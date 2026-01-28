"""Entry point for Wispr Flow."""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import WisprFlowApp


def main():
    """Main entry point."""
    app = WisprFlowApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
