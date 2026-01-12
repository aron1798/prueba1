# ui/components.py - Componentes de UI modernos
import tkinter as tk
from tkinter import ttk

class LoadingSpinner(tk.Canvas):
    """Spinner moderno con animación suave y diseño elegante"""
    def __init__(self, parent, size=80, **kwargs):
        super().__init__(parent, width=size, height=size, 
                        bg='#1e3a5f', highlightthickness=0, **kwargs)
        self.size = size
        self.center = size // 2
        self.radius = size // 3
        self.angle = 0
        self.is_running = False
        self.arcs = []
        
        # Crear múltiples arcos para efecto de gradiente
        colors = ['#4a86e8', '#5a96f8', '#6aa6ff', '#7ab6ff', '#8ac6ff']
        for i, color in enumerate(colors):
            arc = self.create_arc(
                self.center - self.radius,
                self.center - self.radius,
                self.center + self.radius,
                self.center + self.radius,
                start=i * 72,
                extent=50,
                fill='',
                outline=color,
                width=6,
                style='arc'
            )
            self.arcs.append(arc)
    
    def start(self):
        """Inicia la animación del spinner"""
        self.is_running = True
        self.animate()
    
    def stop(self):
        """Detiene la animación del spinner"""
        self.is_running = False
    
    def animate(self):
        """Animación suave del spinner"""
        if not self.is_running:
            return
        
        self.angle = (self.angle + 5) % 360
        
        for i, arc in enumerate(self.arcs):
            start_angle = (self.angle + i * 72) % 360
            self.itemconfig(arc, start=start_angle)
        
        self.after(30, self.animate)

class ModernLoadingOverlay(tk.Toplevel):
    """Overlay de carga moderno con blur y sombras"""
    def __init__(self, parent, mensaje="Cargando datos..."):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        
        # Centrar en la pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        width = 400
        height = 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Frame principal con sombra simulada
        shadow_frame = tk.Frame(self, bg='#0d1b2a')
        shadow_frame.place(x=5, y=5, width=width-10, height=height-10)
        
        main_frame = tk.Frame(self, bg='#e6f2ff', relief='flat', bd=0)
        main_frame.place(x=0, y=0, width=width-10, height=height-10)
        
        # Frame interior con degradado visual
        content_frame = tk.Frame(main_frame, bg='#e6f2ff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Icono decorativo
        icon_label = tk.Label(content_frame, text="📊", font=('Arial', 40), 
                             bg='#e6f2ff', fg='#2c5aa0')
        icon_label.pack(pady=(0, 20))
        
        # Spinner moderno
        self.spinner = LoadingSpinner(content_frame, size=80)
        self.spinner.pack(pady=10)
        self.spinner.start()
        
        # Mensaje principal
        self.mensaje_var = tk.StringVar(value=mensaje)
        mensaje_label = tk.Label(content_frame, 
                                 textvariable=self.mensaje_var,
                                 font=('Arial', 14, 'bold'),
                                 bg='#e6f2ff',
                                 fg='#1e3a5f')
        mensaje_label.pack(pady=15)
        
        # Submensaje animado
        self.dots = 0
        self.submensaje_var = tk.StringVar(value="Procesando")
        submensaje_label = tk.Label(content_frame,
                                   textvariable=self.submensaje_var,
                                   font=('Arial', 10),
                                   bg='#e6f2ff',
                                   fg='#4a86e8')
        submensaje_label.pack()
        
        # Animación de puntos
        self.animate_dots()
        
        # Barra de progreso decorativa
        progress_frame = tk.Frame(content_frame, bg='#d1e3ff', height=4)
        progress_frame.pack(fill='x', pady=(20, 0))
        
        self.progress_bar = tk.Frame(progress_frame, bg='#4a86e8', height=4)
        self.progress_bar.pack(side='left', fill='y')
        self.animate_progress()
    
    def animate_dots(self):
        """Anima los puntos del mensaje"""
        if not self.winfo_exists():
            return
        
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.submensaje_var.set(f"Procesando{dots_text}")
        self.after(500, self.animate_dots)
    
    def animate_progress(self):
        """Anima la barra de progreso"""
        if not self.winfo_exists():
            return
        
        current_width = self.progress_bar.winfo_width()
        max_width = 340  # Ancho máximo de la barra
        
        if current_width >= max_width:
            self.progress_bar.place_forget()
            self.progress_bar.pack(side='left', fill='y')
            current_width = 0
        
        new_width = current_width + 3
        self.progress_bar.configure(width=new_width)
        
        self.after(20, self.animate_progress)
    
    def actualizar_mensaje(self, nuevo_mensaje):
        """Actualiza el mensaje del overlay"""
        self.mensaje_var.set(nuevo_mensaje)
    
    def cerrar(self):
        """Cierra el overlay de forma suave"""
        self.spinner.stop()
        self.destroy()