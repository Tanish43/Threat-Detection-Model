# Real-Time Audio-to-Text WebSocket System (Whisper)

## Setup Instructions

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd /path/to/Major-project
   ```

2. **(Recommended) Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install all dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - For MP3/M4A support, make sure you have `ffmpeg` installed on your system.
     - On macOS: `brew install ffmpeg`
     - On Ubuntu: `sudo apt-get install ffmpeg`

---

## Running the WebSocket Server

Start the FastAPI WebSocket server:
```bash
python ws_server.py
```
The server will listen at `ws://localhost:8000/ws/audio`.

---

## Running the Client

### **A. Stream an Audio File (WAV, MP3, M4A)**
```bash
python test_ws_client.py input.wav
```
Replace `input.wav` with your audio file. Supported formats: `.wav`, `.mp3`, `.m4a`.

### **B. Stream from Microphone (Live Audio)**
```bash
python test_ws_client.py --mic
```
Speak into your microphone. Press `Ctrl+C` to stop.

---

## Project Structure

```
Major-project/
├── audio_utils.py
├── beep.wav
├── constants.py
├── input.wav
├── main.py
├── requirements.txt
├── test_ws_client.py
├── ws_server.py
├── .gitignore
└── .venv/           # (not tracked by git)
```

---

## Notes
- All audio is processed in 5-second chunks (16kHz, 16-bit mono PCM).
- The server uses OpenAI Whisper for transcription and fuzzy name detection.
- You can edit `constants.py` to change detection thresholds or the Whisper model. 