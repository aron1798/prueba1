import tkinter as tk
from ui.main_window import MainWindow
# 1. Importar el actualizador
from core.updater import verificar_actualizacion

def main():
    # 2. Verificar actualización ANTES de iniciar la interfaz
    verificar_actualizacion()

    """Punto de entrada principal de la aplicación"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()