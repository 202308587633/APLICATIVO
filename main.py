import tkinter as tk
from controller import ScraperController

if __name__ == "__main__":
    root = tk.Tk()
    # Configuração de alta DPI para telas modernas (opcional, melhora visual)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    app = ScraperController(root)
    root.mainloop()