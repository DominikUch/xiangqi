import asyncio
import websockets
import json
import threading

class NetworkManager:
    def __init__(self, on_move_callback=None, msg_label=None):
        self.peer_ws = None
        self.on_move = on_move_callback
        self.msg_label = msg_label
        self.loop = None

    def start_server(self):
        # Nie używane przy Render (serwer już działa)
        pass

    def connect(self, address):
        def run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._client(address))

        threading.Thread(target=run, daemon=True).start()

    async def _client(self, address):
        try:
            uri = f"wss://{address}" if not address.startswith("ws") else address
            ws = await websockets.connect(uri)
            self.peer_ws = ws

            if self.msg_label:
                try:
                    self.msg_label.config(text="Połączono z serwerem")
                except:
                    pass

            # Wyślij wiadomość inicjalizacyjną
            await ws.send(json.dumps({"type": "hello"}))

            async for msg in ws:
                data = json.loads(msg)
                if self.on_move:
                    self.on_move(data)

        except Exception as e:
            print("Błąd połączenia:", e)
            if self.msg_label:
                try:
                    self.msg_label.config(text=f"Błąd: {e}")
                except:
                    pass

    def send(self, move):
        if not self.peer_ws:
            return

        async def _send():
            try:
                await self.peer_ws.send(json.dumps(move))
            except Exception as e:
                print("Błąd wysyłania:", e)

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_send(), self.loop)

    def close(self):
        if self.peer_ws:
            asyncio.run_coroutine_threadsafe(self.peer_ws.close(), self.loop)
