import asyncio
import json
import websockets

class NetworkManager:
    def __init__(self, loop, on_move_callback, msg_label=None):
        self.loop = loop
        self.on_move = on_move_callback
        self.msg_label = msg_label
        self.peer_ws = None
        self.server = None

    def start_server(self, host="0.0.0.0", port=8765):
        async def handler(websocket):
            self.peer_ws = websocket
            if self.msg_label:
                try: self.msg_label.config(text="Ktoś połączył się")
                except: pass
            try:
                async for msg in websocket:
                    self.on_move(json.loads(msg))
            except:
                if self.msg_label:
                    try: self.msg_label.config(text="Połączenie zamknięte")
                    except: pass

        async def serve():
            self.server = await websockets.serve(handler, host, port)
            await self.server.wait_closed()

        asyncio.run_coroutine_threadsafe(serve(), self.loop)

    def connect(self, address):
        if not address.startswith("ws://") and not address.startswith("wss://"):
            address = "ws://"+address

        async def client():
            try:
                ws = await websockets.connect(address)
                self.peer_ws = ws
                if self.msg_label:
                    try: self.msg_label.config(text="Połączono")
                    except: pass
                async for msg in ws:
                    self.on_move(json.loads(msg))
            except Exception as e:
                if self.msg_label:
                    try: self.msg_label.config(text=f"Błąd: {e}")
                    except: pass

        asyncio.run_coroutine_threadsafe(client(), self.loop)

    def send_move(self, src, dst):
        if not self.peer_ws:
            if self.msg_label:
                try: self.msg_label.config(text="Brak połączenia")
                except: pass
            return
        move = {"src": list(src), "dst": list(dst)}
        try:
            asyncio.run_coroutine_threadsafe(self.peer_ws.send(json.dumps(move)), self.loop)
        except Exception as e:
            if self.msg_label:
                try: self.msg_label.config(text=f"Błąd wysyłania: {e}")
                except: pass
