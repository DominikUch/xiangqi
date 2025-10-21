import asyncio
import websockets
import json

connected = set()

async def handler(websocket):
    print("Nowe połączenie!")
    connected.add(websocket)
    try:
        async for message in websocket:
            print("Otrzymano:", message)
            # Prześlij wiadomość do wszystkich innych klientów
            for conn in connected:
                if conn != websocket:
                    await conn.send(message)
    except websockets.exceptions.ConnectionClosed:
        print("Połączenie zakończone")
    finally:
        connected.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("Serwer działa na porcie 8765")
        await asyncio.Future()  # działa wiecznie

if __name__ == "__main__":
    asyncio.run(main())
