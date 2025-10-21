import tkinter as tk
from gui.base_gui import BaseXiangqiGUI

class SingleplayerGUI(BaseXiangqiGUI):
    def __init__(self, master, return_to_menu_callback):
        # przekazanie callbacku do klasy bazowej
        super().__init__(master, return_to_menu_callback=return_to_menu_callback)
        self.master.title("Xiangqi — Singleplayer")
