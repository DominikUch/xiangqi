import asyncio
import json
import websockets
import os

class NetworkManager:
    def __init__(self, loop, on_move_callback, msg_label=None):
        self.loop = loop
        self.on_move = on_move_callback
        self.msg_label = msg_label
        self.peer_ws = None
        self.server = None

    # --- URUCHOMIENIE SERWERA ---
    def start_server(self, host="0.0.0.0"):
        port = int(os.environ.get("PORT", 8765))  # Render ustawia PORT automatycznie

        async def handler(websocket):
            self.peer_ws = websocket
            if self.msg_label:
                try: self.msg_label.config(text="Ktoś połączył się")
                except: pass
            try:
                async for msg in websocket:
                    self.on_move(json.loads(msg))
            except Exception as e:
                if self.msg_label:
                    try: self.msg_label.config(text=f"Połączenie zamknięte: {e}")
                    except: pass

        async def serve():
            self.server = await websockets.serve(handler, host, port)
            if self.msg_label:
                try: self.msg_label.config(text=f"Hosting na porcie {port}")
                except: pass
            await self.server.wait_closed()

        asyncio.run_coroutine_threadsafe(serve(), self.loop)

    # --- POŁĄCZENIE Z SERWEREM ---
    def connect(self, address):
        # upewniamy się, że jest prefiks wss:// (Render działa po HTTPS)
        if not address.startswith("ws://") and not address.startswith("wss://"):
            address = "wss://" + address

        async def client():
            try:
                ws = await websockets.connect(address)
                self.peer_ws = ws
                if self.msg_label:
                    try: self.msg_label.config(text="Połączono z serwerem")
                    except: pass

                async for msg in ws:
                    self.on_move(json.loads(msg))
            except Exception as e:
                if self.msg_label:
                    try: self.msg_label.config(text=f"Błąd połączenia: {e}")
                    except: pass

        asyncio.run_coroutine_threadsafe(client(), self.loop)

    # --- WYSYŁANIE RUCHU ---
    def send_move(self, src, dst):
        if not self.peer_ws:
            if self.msg_label:
                try: self.msg_label.config(text="Brak połączenia z serwerem")
                except: pass
            return

        move = {"src": list(src), "dst": list(dst)}
        try:
            asyncio.run_coroutine_threadsafe(self.peer_ws.send(json.dumps(move)), self.loop)
        except Exception as e:
            if self.msg_label:
                try: self.msg_label.config(text=f"Błąd wysyłania: {e}")
                except: pass
