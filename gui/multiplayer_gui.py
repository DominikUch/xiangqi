import tkinter as tk
import threading
import asyncio
from gui.base_gui import BaseXiangqiGUI
from network import NetworkManager
from game_logic import is_legal_move, get_legal_moves


class MultiplayerGUI(BaseXiangqiGUI):
    def __init__(self, master, return_to_menu_callback):
        # przekazanie callbacka do klasy bazowej
        super().__init__(master, return_to_menu_callback=return_to_menu_callback)
        self.master.title("Xiangqi — Multiplayer")

        # --- kontrolki host/connect ---
        self.controls_frame = tk.Frame(self.master)
        self.controls_frame.pack(pady=10)

        self.host_btn = tk.Button(self.controls_frame, text="Host", command=self.start_server)
        self.connect_btn = tk.Button(self.controls_frame, text="Połącz", command=self.connect_to_server)
        self.addr_entry = tk.Entry(self.controls_frame)
        self.msg_label = tk.Label(self.master, text="")

        self.host_btn.pack(side="left", padx=5)
        self.connect_btn.pack(side="left", padx=5)
        self.addr_entry.pack(side="left", padx=5)
        self.msg_label.pack()

        # --- konfiguracja sieci ---
        self.my_color = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.network = NetworkManager(self.loop, self.apply_remote_move, self.msg_label)

        # --- flaga stanu gry ---
        self.game_active = True

    # --- start serwera ---
    def start_server(self):
        self.my_color = 'r'
        self.network.start_server()
        self.msg_label.config(text="Hosting na porcie 8765")
        self._hide_controls()

    # --- połączenie do serwera ---
    def connect_to_server(self):
        self.my_color = 'b'
        addr = self.addr_entry.get()
        self.network.connect(addr)
        self.msg_label.config(text="Łączenie...")
        self._hide_controls()

    # --- ukrycie kontrolek po połączeniu ---
    def _hide_controls(self):
        self.host_btn.pack_forget()
        self.connect_btn.pack_forget()
        self.addr_entry.pack_forget()

    # --- wysyłanie ruchu ---
    def send_move(self, src, dst):
        if self.game_active:
            try:
                self.network.send_move(src, dst)
            except Exception:
                pass

    # --- kliknięcia myszką ---
    def on_click(self, event):
        if not self.game_active:
            return

        if self.my_color is None or self.current_player != self.my_color:
            return

        col, row = self.pixel_to_board(event.x, event.y)
        if not (0 <= col < 9 and 0 <= row < 10):
            return

        if self.selected is None:
            if (col, row) in self.pieces and self.pieces[(col, row)][0] == self.current_player:
                self.selected = (col, row)
                self.highlighted_moves = get_legal_moves(self.pieces, self.selected)
        else:
            src = self.selected
            dst = (col, row)
            if dst in self.highlighted_moves:
                self._execute_move(src, dst)
                self.send_move(src, dst)
                self.current_player = 'b' if self.current_player == 'r' else 'r'
            self.selected = None
            self.highlighted_moves = []

        self.draw_highlights()

    # --- wykonanie ruchu otrzymanego z sieci ---
    def apply_remote_move(self, move):
        if not self.game_active:
            return

        src = tuple(move["src"])
        dst = tuple(move["dst"])
        if src in self.pieces and is_legal_move(self.pieces, src, dst):
            self._execute_move(src, dst)
            self.current_player = self.my_color
            self.draw_highlights()
