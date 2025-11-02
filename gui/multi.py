# gui/multi.py
import asyncio
import threading
import tkinter as tk
import random
from gui.base_gui import BaseXiangqiGUI
from aiortc import RTCPeerConnection, RTCDataChannel, RTCSessionDescription

# --- helpery motywów ---
def get_bg_color(dark):
    return "#2b2b2b" if dark else "#f0f0f0"

def get_fg_color(dark):
    return "#ffffff" if dark else "#000000"

# --- obsługa online ---
class Online:
    def __init__(self, update_message_callback, execute_remote_move):
        self.loop = asyncio.new_event_loop()
        self.pc = RTCPeerConnection()
        self.channel = None
        self.update_message_callback = update_message_callback
        self.execute_remote_move = execute_remote_move
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    def on_datachannel(self, channel: RTCDataChannel):
        self.channel = channel
        self.channel.on("message", self.handle_message)

    async def create_offer(self):
        self.channel = self.pc.createDataChannel("game")
        self.channel.on("message", self.handle_message)
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        return self.pc.localDescription.sdp

    async def apply_answer(self, sdp):
        answer = RTCSessionDescription(sdp=sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

    async def create_answer(self, sdp):
        self.pc.on("datachannel", self.on_datachannel)
        offer = RTCSessionDescription(sdp=sdp, type="offer")
        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return self.pc.localDescription.sdp

    async def send_message_async(self, message):
        if self.channel and self.channel.readyState == "open":
            self.channel.send(str(message))

    def handle_message(self, message):
        if message.startswith("MOVE:"):
            # wiadomość ruchu w formacie: MOVE:src_col,src_row->dst_col,dst_row
            parts = message[5:].split("->")
            src = tuple(map(int, parts[0].split(",")))
            dst = tuple(map(int, parts[1].split(",")))
            self.execute_remote_move(src, dst)
        else:
            self.update_message_callback(f"Peer: {message}")

# --- GUI multiplayer z planszą i chatem ---
class MultiplayerGUI(BaseXiangqiGUI):
    def __init__(self, master, is_initiator, dark_theme=False, return_to_menu_callback=None):
        self.dark = dark_theme
        self.is_initiator = is_initiator
        self.online = Online(self.update_chat, self.remote_move)

        # --- ustalanie kolorów graczy ---
        if self.is_initiator:
            self.player_color = random.choice(['r', 'b'])
        else:
            self.player_color = None  # kolor zostanie ustawiony po odebraniu SDP

        super().__init__(master, player_color=self.player_color, return_to_menu_callback=return_to_menu_callback)

        # czerwony zawsze zaczyna
        self.my_turn = (self.player_color == 'r') if self.player_color else False

        # --- chat po prawej stronie ---
        self.chat_frame = tk.Frame(self.main_frame, bd=2, relief="groove",
                                   bg=get_bg_color(self.dark))
        self.chat_frame.grid(row=0, column=2, padx=10, sticky="ns")

        self.chat_label = tk.Label(self.chat_frame, text="💬 Chat użytkowników",
                                   bg=get_bg_color(self.dark),
                                   fg=get_fg_color(self.dark),
                                   font=("Arial", 10, "bold"))
        self.chat_label.pack(anchor="w", padx=5, pady=(5,0))

        self.message_box = tk.Text(self.chat_frame, state='disabled', width=40, height=30,
                                   bg=get_bg_color(self.dark),
                                   fg=get_fg_color(self.dark))
        self.message_box.pack(padx=5, pady=(2,5))

        tk.Label(self.chat_frame, text="Wpisz wiadomość i naciśnij Enter:",
                 bg=get_bg_color(self.dark),
                 fg=get_fg_color(self.dark),
                 font=("Arial", 10, "italic")).pack(pady=(0,0))

        self.entry = tk.Entry(self.chat_frame, width=40, font=("Arial", 12),
                              bg="#1e1e1e" if self.dark else "#ffffff",
                              fg=get_fg_color(self.dark),
                              bd=2, relief="groove",
                              insertbackground=get_fg_color(self.dark))
        self.entry.pack(padx=5, pady=(2,5))
        self.entry.bind("<Return>", self.send_message)

        # --- inicjalizacja połączenia WebRTC ---
        if self.is_initiator:
            self.start_offer()
        else:
            self.sdp_window()

    # --- logika SDP dla inicjatora ---
    def start_offer(self):
        asyncio.run_coroutine_threadsafe(
            self.online.create_offer(),
            self.online.loop
        ).add_done_callback(self.offer_ready)

    def offer_ready(self, future):
        sdp = future.result()
        # inicjator wysyła kolor gracza w SDP
        sdp += f"\nCOLOR:{self.player_color}"
        self.sdp_window(offer_sdp=sdp)

    def sdp_window(self, offer_sdp=None):
        win = tk.Toplevel(self.master)
        win.title("SDP Exchange")
        tk.Label(win, text="Wklej SDP przeciwnika i naciśnij Enter").pack(pady=5)
        sdp_entry = tk.Entry(win, width=80)
        sdp_entry.pack(pady=5)
        result_box = tk.Text(win, height=10, width=80)
        result_box.pack(pady=5)

        def submit_sdp():
            sdp_text = sdp_entry.get()
            sdp_entry.delete(0, tk.END)
            # --- ustalanie kolorów dla drugiego gracza ---
            for line in sdp_text.splitlines():
                if line.startswith("COLOR:"):
                    self.player_color = 'b' if line[6:] == 'r' else 'r'
                    self.my_turn = (self.player_color == 'r')
                    break

            if self.is_initiator:
                asyncio.run_coroutine_threadsafe(
                    self.online.apply_answer(sdp_text),
                    self.online.loop
                )
            else:
                asyncio.run_coroutine_threadsafe(
                    self.online.create_answer(sdp_text),
                    self.online.loop
                ).add_done_callback(lambda f: result_box.insert("1.0", f.result()))

        tk.Button(win, text="Submit SDP", command=submit_sdp).pack(pady=5)

        if offer_sdp:
            result_box.insert("1.0", offer_sdp)

    # --- wysyłanie wiadomości ---
    def send_message(self, event=None):
        msg = self.entry.get()
        if not msg.strip():
            return
        self.entry.delete(0, tk.END)
        self.update_chat(f"You: {msg}")
        asyncio.run_coroutine_threadsafe(
            self.online.send_message_async(msg),
            self.online.loop
        )

    def update_chat(self, message):
        self.message_box.config(state='normal')
        self.message_box.insert(tk.END, message + "\n")
        self.message_box.see(tk.END)
        self.message_box.config(state='disabled')

    # --- wykonanie ruchu lokalnego i wysłanie go do przeciwnika ---
    def _execute_move(self, src, dst, remote=False):
        super()._execute_move(src, dst, remote)
        if not remote:
            msg = f"MOVE:{src[0]},{src[1]}->{dst[0]},{dst[1]}"
            asyncio.run_coroutine_threadsafe(
                self.online.send_message_async(msg),
                self.online.loop
            )
            self.my_turn = False  # po ruchu kończy się tura lokalnego gracza

    # --- wykonanie ruchu przeciwnika ---
    def remote_move(self, src, dst):
        self._execute_move(src, dst, remote=True)
        # po ruchu przeciwnika zaczyna się tura lokalnego gracza
        self.my_turn = True
