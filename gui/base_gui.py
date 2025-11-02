import tkinter as tk
from PIL import Image, ImageTk
import os
from game_logic import (
    INITIAL_POSITIONS, COLS, ROWS, CELL, MARGIN,
    get_legal_moves, move_piece
)

class BaseXiangqiGUI:
    def __init__(self, master, player_color='r', return_to_menu_callback=None):
        self.master = master
        self.return_to_menu_callback = return_to_menu_callback
        self.player_color = player_color  # 'r' lub 'b'
        self.width = MARGIN * 2 + CELL * (COLS - 1)
        self.height = MARGIN * 2 + CELL * (ROWS - 1)
        self.rotated = False  # status obrotu

        # --- główny frame planszy + historia + przycisk ---
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(expand=True, pady=40)
        self.main_frame.pack_propagate(False)

        # --- Canvas planszy ---
        self.canvas = tk.Canvas(self.main_frame, width=self.width, height=self.height,
                                bg="#f8f0d8", highlightthickness=0)
        self.canvas.grid(row=0, column=0)

        # --- Panel historii ruchów ---
        self.history_frame = tk.Frame(self.main_frame)
        self.history_frame.grid(row=0, column=1, padx=10)
        tk.Label(self.history_frame, text="Historia ruchów", font=("Arial", 12, "bold")).pack()
        self.history_listbox = tk.Listbox(self.history_frame, width=20, height=35)
        self.history_listbox.pack()

        # --- przyciski poniżej planszy ---
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, pady=5)

        # --- przycisk obracania planszy ---
        self.rot_btn = tk.Button(self.button_frame, text="Obróć planszę", font=("Arial", 10, "bold"),
                                 command=self.rotate_board)
        self.rot_btn.pack(side="left", padx=5)

        # --- przycisk Menu ---
        self.menu_btn = tk.Button(self.button_frame, text="Menu", font=("Arial", 10, "bold"),
                                  command=self._on_menu)
        self.menu_btn.pack(side="left", padx=5)

        # --- inicjalizacja planszy ---
        self.pieces = dict(INITIAL_POSITIONS)
        self.selected = None
        self.highlighted_moves = []
        self.current_player = 'r'
        self.move_history = []

        # --- wczytanie grafik ---
        self.piece_images = {}
        assets_path = os.path.join(os.path.dirname(__file__), "..", "assets")
        label_to_file = {
            'K': 'king', 'A': 'advisor', 'E': 'elephant',
            'Kn': 'knight', 'R': 'rock', 'C': 'cannon', 'P': 'pawn'
        }
        for color in ['r','b']:
            for label, fname in label_to_file.items():
                file_path = os.path.join(assets_path, f"{fname}_{'red' if color=='r' else 'black'}.png")
                if os.path.exists(file_path):
                    img = Image.open(file_path).resize((int(CELL*0.8), int(CELL*0.8)), Image.Resampling.LANCZOS)
                    self.piece_images[(color,label)] = ImageTk.PhotoImage(img)

        # --- rysowanie planszy i figur ---
        self.draw_board()
        self.draw_pieces()
        self.draw_highlights()

        # --- bind kliknięcia ---
        self.canvas.bind("<Button-1>", self.on_click)

    # --- obsługa przycisku Menu ---
    def _on_menu(self):
        if self.return_to_menu_callback:
            self.destroy_widgets()
            self.return_to_menu_callback()

    # --- konwersja współrzędnych z widoku ---
    def view_coords(self, col, row):
        if self.rotated or self.player_color == 'b':
            return COLS - 1 - col, ROWS - 1 - row
        return col, row

    def board_to_pixel(self, col, row):
        col_v, row_v = self.view_coords(col, row)
        return MARGIN + col_v * CELL, MARGIN + row_v * CELL

    def pixel_to_board(self, x, y):
        col = round((x - MARGIN)/CELL)
        row = round((y - MARGIN)/CELL)
        if self.rotated or self.player_color == 'b':
            col, row = COLS - 1 - col, ROWS - 1 - row
        return col, row

    # --- rysowanie planszy ---
    def draw_board(self):
        self.canvas.delete("board")
        # linie pionowe
        for c in range(COLS):
            x1, y1 = self.board_to_pixel(c, 0)
            x2, y2 = self.board_to_pixel(c, 4)
            x3, y3 = self.board_to_pixel(c, 5)
            x4, y4 = self.board_to_pixel(c, 9)
            if 0 < c < COLS-1:
                self.canvas.create_line(x1, y1, x2, y2, width=2, tags="board")
                self.canvas.create_line(x3, y3, x4, y4, width=2, tags="board")
            else:
                self.canvas.create_line(x1, y1, x4, y4, width=2, tags="board")

        # linie poziome
        for r in range(ROWS):
            x1, y1 = self.board_to_pixel(0, r)
            x2, y2 = self.board_to_pixel(COLS-1, r)
            self.canvas.create_line(x1, y1, x2, y2, width=2, tags="board")

        # rzeka
        ry1 = self.board_to_pixel(0, 4)[1]
        ry2 = self.board_to_pixel(0, 5)[1]
        self.canvas.create_rectangle(MARGIN, ry1, MARGIN + CELL*(COLS-1), ry2, fill="#d0e7f7", outline="", tags="board")
        self.canvas.create_text(self.width//2, (ry1+ry2)/2, font=("Arial",16,"bold"), text="RZEKA", tags="board")

        # pałace
        palace_coords = [(3,0),(3,7)]
        for px, py in palace_coords:
            x1, y1 = self.board_to_pixel(px, py)
            x2, y2 = self.board_to_pixel(px+2, py+2)
            x3, y3 = self.board_to_pixel(px+2, py)
            x4, y4 = self.board_to_pixel(px, py+2)
            self.canvas.create_line(x1, y1, x2, y2, width=2, tags="board")
            self.canvas.create_line(x3, y3, x4, y4, width=2, tags="board")

        # indeksy kolumn (na górze i dole planszy)
        col_labels = ['A','B','C','D','E','F','G','H','I']
        for c, label in enumerate(col_labels):
            x = MARGIN + c * CELL
            y_top = MARGIN - 32
            y_bot = MARGIN + (ROWS - 1) * CELL + 32
            self.canvas.create_text(x, y_top, text=label, font=("Arial",12,"bold"), tags="board")
            self.canvas.create_text(x, y_bot, text=label, font=("Arial",12,"bold"), tags="board")

        # indeksy rzędów (po lewej i prawej planszy)
        for r in range(ROWS):
            y = MARGIN + r * CELL
            x_left = MARGIN - 32
            x_right = MARGIN + (COLS - 1) * CELL + 32
            self.canvas.create_text(x_left, y, text=str(r+1), font=("Arial",12,"bold"), tags="board")
            self.canvas.create_text(x_right, y, text=str(r+1), font=("Arial",12,"bold"), tags="board")

    # --- rysowanie figur ---
    def draw_pieces(self):
        self.piece_ids = {}
        for pos, (color,label) in self.pieces.items():
            x, y = self.board_to_pixel(*pos)
            img = self.piece_images.get((color,label))
            if img:
                img_id = self.canvas.create_image(x, y, image=img)
                self.piece_ids[pos] = img_id
                self.canvas.tag_raise(img_id)

    # --- highlights i selekcja ---
    def draw_highlights(self):
        self.canvas.delete("highlight")
        for col,row in self.highlighted_moves:
            x,y = self.board_to_pixel(col,row)
            r = CELL*0.15 if (col,row) not in self.pieces else CELL*0.4
            outline = "red" if (col,row) in self.pieces else ""
            fill = "green" if (col,row) not in self.pieces else ""
            self.canvas.create_oval(x-r, y-r, x+r, y+r, outline=outline, fill=fill,
                                    width=8 if (col,row) in self.pieces else 0, tags="highlight")
        if self.selected:
            col,row = self.selected
            x,y = self.board_to_pixel(col,row)
            r = CELL*0.45
            self.canvas.create_rectangle(x-r, y-r, x+r, y+r, outline="blue", width=3, tags="highlight")

    # --- wykonanie ruchu ---
    def _execute_move(self, src, dst, remote=False):
        """Wykonaj ruch i opcjonalnie dodaj go do historii."""
        if dst in self.pieces:
            captured_id = self.piece_ids.pop(dst)
            self.canvas.delete(captured_id)

        img_id = self.piece_ids.pop(src)
        x, y = self.board_to_pixel(*dst)
        self.canvas.coords(img_id, x, y)
        self.piece_ids[dst] = img_id
        move_piece(self.pieces, src, dst)
        self.canvas.tag_raise(img_id)

        # --- zapis historii z kolorem figury i numeracją ruchów ---
        piece_color, piece_label = self.pieces.get(dst, ('',''))
        color_prefix = "(red)" if piece_color == 'r' else "(black)"
        move_number = len(self.move_history) + 1  # numer kolejnego ruchu
        move_str = f"{move_number}. {color_prefix} {piece_label} {self.pos_to_label(src)} -> {self.pos_to_label(dst)}"

        if not remote:
            self.move_history.append(move_str)
            self.history_listbox.insert(tk.END, move_str)
            self.history_listbox.yview(tk.END)
        else:
            # remote move również dodajemy do historii
            self.move_history.append(move_str)
            self.history_listbox.insert(tk.END, move_str)
            self.history_listbox.yview(tk.END)



    def pos_to_label(self, pos):
        col, row = pos
        col_label = ['A','B','C','D','E','F','G','H','I'][col]
        row_label = str(row+1)
        return f"{col_label}{row_label}"

    def on_click(self, event):
        col, row = self.pixel_to_board(event.x, event.y)
        if not (0<=col<COLS and 0<=row<ROWS):
            return

        # --- nowa kontrola: ruch tylko swoim kolorem ---
        if hasattr(self, "my_turn") and not self.my_turn:
            return

        if self.selected is None:
            if (col,row) in self.pieces and self.pieces[(col,row)][0]==self.player_color:
                self.selected = (col,row)
                self.highlighted_moves = get_legal_moves(self.pieces, self.selected)
        else:
            src,dst = self.selected,(col,row)
            if dst in self.highlighted_moves:
                self._execute_move(src,dst)
                if hasattr(self, "my_turn"):
                    self.my_turn = False  # po ruchu kończy się tura lokalnego gracza
            self.selected = None
            self.highlighted_moves = []
        self.draw_highlights()

    def rotate_board(self):
        self.rotated = not self.rotated
        self.draw_board()
        for pos, img_id in self.piece_ids.items():
            x, y = self.board_to_pixel(*pos)
            self.canvas.coords(img_id, x, y)
            self.canvas.tag_raise(img_id)
        self.draw_highlights()

    # --- metoda do czyszczenia GUI przy powrocie do menu ---
    def destroy_widgets(self):
        """
        Usuwa wszystkie widgety utworzone przez BaseXiangqiGUI,
        czyli planszę, ramki, przyciski itp.
        """
        # usuń główny frame z całą zawartością (plansza, historia, obrót)
        try:
            self.main_frame.destroy()
        except Exception:
            pass

        # usuń przycisk menu, jeśli istnieje
        if hasattr(self, "menu_btn") and self.menu_btn.winfo_exists():
            try:
                self.menu_btn.destroy()
            except Exception:
                pass

        # usuń inne potencjalne elementy GUI (np. kontrolki multiplayera)
        for widget in getattr(self.master, "winfo_children", lambda: [])():
            # nie ruszamy głównego okna, tylko dzieci (frames, buttons itd.)
            if isinstance(widget, tk.Widget):
                try:
                    widget.destroy()
                except Exception:
                    pass

