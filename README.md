# Wispr Flow

Voice-to-text Windows app that records voice via hotkey, transcribes locally with Whisper, formats with GPT, and auto-pastes the result.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your OpenAI API key (optional, for text formatting):
   ```bash
   set OPENAI_API_KEY=your-key-here
   ```

3. Run the app:
   ```bash
   python run.py
   ```

## Usage

- **Hold** `Ctrl+Shift+Space` to start recording
- **Release** to stop recording and transcribe
- Text is automatically pasted to the active window

## Overlay Colors

- Gray: Idle
- Red: Recording
- Yellow: Processing (transcribing/formatting)
- Green: Pasting
- Orange: Error

## Configuration

Edit `config/default_config.yaml` to customize:
- Whisper model (default: base.en)
- OpenAI model and prompt
- Overlay position and size
- Auto-paste behavior

## Building Executable

```bash
pip install pyinstaller
pyinstaller build.spec
```

The executable will be in the `dist` folder.
