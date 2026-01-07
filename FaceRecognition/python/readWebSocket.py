import asyncio
import json
import websockets
import requests

WS_URL = "ws://localhost:8000/stream/audio"

async def listen_ws():
    # Connect to the WebSocket server
    async with websockets.connect(WS_URL) as websocket:
        print("Connected to WebSocket")

        while True:
            try:
                # Receive a message from the WebSocket
                message = await websocket.recv()

                # Parse the message as JSON
                data = json.loads(message)

                # Check trigger conditions
                if (
                    data.get("type") == "meta"
                    and isinstance(data.get("content"), dict)
                    and data["content"].get("type") == "json"
                ):
                    # Triggered logic
                    handle_meta_json(data)

            except json.JSONDecodeError:
                # Ignore non-JSON messages
                continue
            except websockets.ConnectionClosed:
                print("WebSocket connection closed")
                break

def handle_meta_json(data):
    url = 'http://localhost:5006/save_image'

    requests.post(url, json = data["content"]["content"])

if __name__ == "__main__":
    # Start the asyncio event loop
    asyncio.run(listen_ws())
