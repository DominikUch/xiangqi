import asyncio
import json
import websockets
import os

PORT = int(os.environ.get("PORT", 8765))  # Render automatycznie ustawia PORT

async def handler(websocket):
    print("Nowe połączenie")
    try:
        async for msg in websocket:
            print("Otrzymano:", msg)
            # tutaj można np. odesłać wiadomość z powrotem:
            await websocket.send(json.dumps({"ok": True, "echo": msg}))
    except Exception as e:
        print("Rozłączono:", e)

async def main():
    print(f"Serwer startuje na porcie {PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()  # działa wiecznie

if __name__ == "__main__":
    asyncio.run(main())
