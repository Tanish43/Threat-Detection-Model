import asyncio
import websockets
import sys
import time
import os

CHUNK_SIZE = 160000  # 5 seconds of 16kHz, 16-bit mono audio

def get_pcm_audio_bytes(audio_path):
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == ".wav":
        import wave
        with wave.open(audio_path, "rb") as wf:
            if wf.getframerate() != 16000 or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(audio_path)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                return audio.raw_data
            else:
                return wf.readframes(wf.getnframes())
    elif ext in [".mp3", ".m4a"]:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        return audio.raw_data
    else:
        raise ValueError("Unsupported file type. Use WAV, MP3, or M4A.")

async def stream_audio(audio_path):
    uri = "ws://localhost:8000/ws/audio"
    audio_bytes = get_pcm_audio_bytes(audio_path)
    async with websockets.connect(uri) as websocket:
        for i in range(0, len(audio_bytes), CHUNK_SIZE):
            chunk = audio_bytes[i:i+CHUNK_SIZE]
            await websocket.send(chunk)
            response = await websocket.recv()
            print("Response:", response)
            time.sleep(5)  # 5 seconds per chunk

async def stream_microphone():
    import sounddevice as sd
    import numpy as np

    uri = "ws://localhost:8000/ws/audio"
    samplerate = 16000
    blocksize = CHUNK_SIZE // 2  # 2 bytes per sample

    print("Speak into the microphone. Press Ctrl+C to stop.")
    async with websockets.connect(uri) as websocket:
        try:
            with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', blocksize=blocksize) as stream:
                while True:
                    audio_chunk, _ = stream.read(blocksize)
                    audio_bytes = audio_chunk.tobytes()
                    await websocket.send(audio_bytes)
                    response = await websocket.recv()
                    print("Response:", response)
                    time.sleep(5)  # 5 seconds per chunk
        except KeyboardInterrupt:
            print("Microphone streaming stopped.")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--mic":
        asyncio.run(stream_microphone())
    elif len(sys.argv) == 2:
        audio_path = sys.argv[1]
        asyncio.run(stream_audio(audio_path))
    else:
        print("Usage:")
        print("  python test_ws_client.py <audio_file.(wav|mp3|m4a)>")
        print("  python test_ws_client.py --mic   # for microphone streaming")
        sys.exit(1)