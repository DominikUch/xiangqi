# main.py
import tkinter as tk
from gui.single import SingleplayerGUI
from gui.multi import MultiplayerGUI

# --- globalny motyw ---
DARK_THEME = False
ALL_WINDOWS = []  # wszystkie główne okna i Toplevel


def get_bg_color():
    return "#2b2b2b" if DARK_THEME else "#f0f0f0"


def get_fg_color():
    return "#ffffff" if DARK_THEME else "#000000"


def apply_theme_recursive(widget):
    """Rekurencyjnie zmienia kolory dla wszystkich widgetów oprócz Canvas i sprawdzając czy istnieją."""
    if not widget.winfo_exists():
        return
    if isinstance(widget, tk.Canvas):
        return  # plansza nie ruszana

    bg_color = get_bg_color()
    fg_color = get_fg_color()

    try:
        widget.config(bg=bg_color)
    except tk.TclError:
        pass

    if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton, tk.Radiobutton)):
        try:
            widget.config(fg=fg_color)
        except tk.TclError:
            pass

    if isinstance(widget, tk.Button):
        try:
            widget.config(activebackground="#555555" if DARK_THEME else "#d9d9d9",
                          activeforeground=fg_color)
        except tk.TclError:
            pass

    if isinstance(widget, tk.Listbox):
        try:
            widget.config(fg=fg_color,
                          selectbackground="#444444" if DARK_THEME else "#c0c0ff",
                          selectforeground=fg_color)
        except tk.TclError:
            pass

    if isinstance(widget, (tk.Entry, tk.Text)):
        try:
            widget.config(fg=fg_color, insertbackground=fg_color)
        except tk.TclError:
            pass

    if isinstance(widget, (tk.Frame, tk.Toplevel)):
        try:
            widget.config(bg=bg_color)
        except tk.TclError:
            pass

    for child in widget.winfo_children():
        apply_theme_recursive(child)


def apply_theme_global():
    """Odświeża motyw we wszystkich oknach zarejestrowanych w ALL_WINDOWS."""
    for window in ALL_WINDOWS:
        if window.winfo_exists():
            apply_theme_recursive(window)


class StartScreen:
    def __init__(self, master):
        self.master = master
        if master not in ALL_WINDOWS:
            ALL_WINDOWS.append(master)

        self.master.geometry("1200x800")
        self.frame = tk.Frame(master)
        self.frame.pack(expand=True)
        apply_theme_recursive(self.frame)

        tk.Label(self.frame, text="Wybierz tryb gry", font=("Arial", 24, "bold"),
                 bg=get_bg_color(), fg=get_fg_color()).pack(pady=30)

        tk.Button(self.frame, text="Singleplayer", width=25, height=2, font=("Arial", 16),
                  command=self.start_singleplayer).pack(pady=10)
        tk.Button(self.frame, text="Multiplayer", width=25, height=2, font=("Arial", 16),
                  command=self.start_multiplayer).pack(pady=10)
        tk.Button(self.frame, text="Ustawienia", width=25, height=2, font=("Arial", 16),
                  command=self.show_settings).pack(pady=10)
        tk.Button(self.frame, text="Tutorial", width=25, height=2, font=("Arial", 16),
                  command=self.show_tutorial).pack(pady=10)

    def start_singleplayer(self):
        self.frame.destroy()
        gui = SingleplayerGUI(self.master, self.show_menu)
        if gui.main_frame not in ALL_WINDOWS:
            ALL_WINDOWS.append(gui.main_frame)
        apply_theme_global()

    def start_multiplayer(self):
        self.frame.destroy()

        # Pytanie, czy użytkownik jest inicjatorem
        win = tk.Toplevel(self.master)
        win.title("Multiplayer Setup")
        if win not in ALL_WINDOWS:
            ALL_WINDOWS.append(win)
        win.geometry("400x200")
        apply_theme_recursive(win)

        tk.Label(win, text="Czy jesteś inicjatorem połączenia?", font=("Arial", 14),
                 bg=get_bg_color(), fg=get_fg_color()).pack(pady=20)

        def launch_chat(is_initiator):
            win.destroy()
            chat_app = MultiplayerGUI(self.master, is_initiator)


        tk.Button(win, text="Tak", width=15, font=("Arial", 12),
                  command=lambda: launch_chat(True)).pack(pady=5)
        tk.Button(win, text="Nie", width=15, font=("Arial", 12),
                  command=lambda: launch_chat(False)).pack(pady=5)

    def show_menu(self):
        # odtworzenie ekranu startowego
        self.__init__(self.master)

    def show_tutorial(self):
        win = tk.Toplevel(self.master)
        win.title("Tutorial Xiangqi")
        win.geometry("700x500")
        if win not in ALL_WINDOWS:
            ALL_WINDOWS.append(win)

        text = tk.Text(win, wrap="word", font=("Arial", 12),
                       bg="#3c3c3c" if DARK_THEME else "white",
                       fg=get_fg_color())
        text.pack(expand=True, fill="both", padx=10, pady=10)

        tutorial_text = """🇨🇳 TUTORIAL: ZASADY GRY XIANGQI (Chińskie szachy)

CEL GRY:
- Celem jest zbicie króla przeciwnika („K”).

PLANSZA:
- Plansza ma 9 kolumn i 10 rzędów.
- Pośrodku znajduje się „RZEKA”, której nie mogą przekroczyć słonie (B).

RZĄDY FIGUR:
- K (Król): porusza się o jedno pole w pionie lub poziomie, ale tylko w obrębie pałacu (3x3).
- A (Doradca): porusza się o jedno pole po przekątnej w obrębie pałacu.
- B (Słoń): porusza się po przekątnej o 2 pola, ale nie może przekroczyć rzeki ani przeskakiwać figur.
- Kn (Koń): porusza się jak koń w szachach, ale nie może być „zablokowany”.
- R (Wieża): porusza się w pionie i poziomie, dowolnie daleko, jeśli nie ma przeszkód.
- Q (Armatka): porusza się jak wieża, ale bije przeskakując dokładnie jedną figurę.
- P (Żołnierz): porusza się o jedno pole do przodu, a po przekroczeniu rzeki także w bok.

KOLEJNOŚĆ RUCHÓW:
- Czerwony (r) zaczyna grę.
- Gracze wykonują ruchy na zmianę.

ZASADY BICIA:
- Figury biją zajmując pole przeciwnika.
- Możliwe pola do bicia są oznaczone czerwonym okręgiem.

POWODZENIA I MIŁEJ GRY!"""
        text.insert("1.0", tutorial_text)
        text.config(state="disabled")
        apply_theme_global()

    def show_settings(self):
        win = tk.Toplevel(self.master)
        win.title("Ustawienia Xiangqi")
        win.geometry("400x300")
        if win not in ALL_WINDOWS:
            ALL_WINDOWS.append(win)
        apply_theme_recursive(win)

        tk.Label(win, text="Ustawienia gry", font=("Arial", 14),
                 bg=get_bg_color(), fg=get_fg_color()).pack(pady=20)

        def toggle_theme():
            global DARK_THEME
            DARK_THEME = not DARK_THEME
            apply_theme_global()

        tk.Button(win, text="Przełącz ciemny motyw", width=25, font=("Arial", 12),
                  command=toggle_theme).pack(pady=10)
        tk.Button(win, text="Zamknij", width=15, font=("Arial", 12),
                  command=win.destroy).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Xiangqi")
    if root not in ALL_WINDOWS:
        ALL_WINDOWS.append(root)
    StartScreen(root)
    root.mainloop()
