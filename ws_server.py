from fastapi import FastAPI, WebSocket
import uvicorn
import json
from audio_utils import process_audio_bytes

app = FastAPI()

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    target_names = "test"  # You can change this or make it dynamic
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            recognized_text, is_beep = process_audio_bytes(audio_bytes, target_names)
            response = {"msg": recognized_text, "isBeep": is_beep}
            await websocket.send_text(json.dumps(response))
    except Exception as e:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("ws_server:app", host="0.0.0.0", port=8000, reload=True)