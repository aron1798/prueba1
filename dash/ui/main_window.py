# ui/main_window.py
import tkinter as tk
from tkinter import messagebox
from core.data_manager import DataManager
from core.navigation import NavigationManager
from modules.ocupabilidad import OcupabilidadModule
from modules.ventas import VentasModule

class MainWindow:
    """Ventana principal del dashboard con sidebar y navegación entre módulos"""
    
    def __init__(self, root):
        """
        Inicializa la ventana principal
        
        Args:
            root: Ventana raíz de Tkinter
        """
        self.root = root
        self.root.title("📊 DASHBOARD PRINCIPAL")
        self.root.configure(bg='#e9f0f8')
        self.root.state('zoomed')  # Maximizar ventana
        self.root.resizable(True, True)
        
        # Inicializar DataManager (compartido por todos los módulos)
        print("🔧 Inicializando DataManager...")
        self.data_manager = DataManager()
        
        # Crear layout principal
        self._create_main_layout()
        
        # Crear NavigationManager
        self.navigation = NavigationManager(self.content_area)
        
        # Inicializar módulos
        self._initialize_modules()
        
        # Registrar callback del sidebar
        self.navigation.registrar_sidebar_callback(self._update_sidebar_active)
        
        # Mostrar módulo inicial (Ocupabilidad)
        self.root.after(100, lambda: self.navigation.cambiar_a("ocupabilidad"))
        
        # Manejo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        print("✅ MainWindow inicializado correctamente")
    
    def _create_main_layout(self):
        """Crea el layout principal: sidebar + área de contenido"""
        # Container principal
        self.main_container = tk.Frame(self.root, bg='#e9f0f8')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar (izquierda)
        self._create_sidebar()
        
        # Área de contenido (derecha)
        self.content_area = tk.Frame(self.main_container, bg='#e9f0f8')
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        print("🎨 Layout principal creado")
    
    def _create_sidebar(self):
        """Crea el sidebar con navegación"""
        self.sidebar = tk.Frame(self.main_container, bg='#12345f', width=240)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Perfil de usuario
        self._create_profile_section()
        
        # Navegación
        self._create_navigation_buttons()
        
        print("📋 Sidebar creado")
    
    def _create_profile_section(self):
        """Crea la sección de perfil en el sidebar"""
        profile_frame = tk.Frame(self.sidebar, bg='#12345f')
        profile_frame.pack(fill=tk.X, pady=30)
        
        # Avatar (círculo decorativo)
        avatar = tk.Canvas(profile_frame, width=80, height=80, bg='#12345f', highlightthickness=0)
        avatar.create_oval(5, 5, 75, 75, fill='#e6f2ff', outline='')
        avatar.pack(padx=20)
        
        # Nombre
        name = tk.Label(profile_frame, text="ADMIN", bg='#12345f', fg='#e6f2ff', 
                       font=('Arial', 12, 'bold'))
        name.pack(padx=10, pady=(8, 0))
        
        # Email
        email = tk.Label(profile_frame, text="admin@empresa.com", bg='#12345f', 
                        fg='#9fc3ff', font=('Arial', 9))
        email.pack(padx=10, pady=(0, 10))
    
    def _create_navigation_buttons(self):
        """Crea los botones de navegación en el sidebar"""
        # Lista de módulos: (nombre_display, icono, nombre_modulo)
        nav_items = [
            ("OCUPABILIDAD", "📈", "ocupabilidad"),
            ("VENTAS", "💼", "ventas"),
        ]
        
        # Diccionario para guardar referencias a los botones
        self.nav_buttons = {}
        
        for nombre_display, icono, nombre_modulo in nav_items:
            # Frame del botón
            btn_frame = tk.Frame(self.sidebar, bg='#12345f', pady=10)
            btn_frame.pack(fill=tk.X)
            
            # Icono
            icon_label = tk.Label(btn_frame, text=icono, bg='#12345f', fg='#e6f2ff', 
                                 font=('Arial', 12))
            icon_label.pack(side=tk.LEFT, padx=(20, 10))
            
            # Texto del botón
            text_label = tk.Label(btn_frame, text=nombre_display, bg='#12345f', 
                                 fg='#e6f2ff', font=('Arial', 11))
            text_label.pack(side=tk.LEFT)
            
            # Guardar referencia al frame del botón
            self.nav_buttons[nombre_modulo] = btn_frame
            
            # Eventos hover
            def on_enter(e, frame=btn_frame):
                frame.config(bg='#1e4a7f')
                for child in frame.winfo_children():
                    child.config(bg='#1e4a7f')
            
            def on_leave(e, frame=btn_frame, modulo=nombre_modulo):
                # Si es el activo, mantener color activo
                if self.navigation.obtener_modulo_actual() == modulo:
                    frame.config(bg='#2a5fa0')
                    for child in frame.winfo_children():
                        child.config(bg='#2a5fa0')
                else:
                    frame.config(bg='#12345f')
                    for child in frame.winfo_children():
                        child.config(bg='#12345f')
            
            def on_click(e, modulo=nombre_modulo):
                self.navigation.cambiar_a(modulo)
            
            # Bind eventos
            btn_frame.bind('<Enter>', on_enter)
            btn_frame.bind('<Leave>', on_leave)
            btn_frame.bind('<Button-1>', on_click)
            
            icon_label.bind('<Enter>', on_enter)
            icon_label.bind('<Leave>', on_leave)
            icon_label.bind('<Button-1>', on_click)
            
            text_label.bind('<Enter>', on_enter)
            text_label.bind('<Leave>', on_leave)
            text_label.bind('<Button-1>', on_click)
        
        print("🔘 Botones de navegación creados")
    
    def _initialize_modules(self):
        """Inicializa todos los módulos del dashboard"""
        print("🚀 Inicializando módulos...")
        
        try:
            # Módulo Ocupabilidad
            print("  📊 Creando módulo Ocupabilidad...")
            self.ocupabilidad = OcupabilidadModule(self.content_area, self.data_manager)
            self.navigation.registrar_modulo("ocupabilidad", self.ocupabilidad)
            
            # Módulo Ventas
            print("  💼 Creando módulo Ventas...")
            self.ventas = VentasModule(self.content_area, self.data_manager)
            self.navigation.registrar_modulo("ventas", self.ventas)
            
            print("✅ Todos los módulos inicializados correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando módulos: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error al inicializar módulos: {e}")
    
    def _update_sidebar_active(self, modulo_activo):
        """
        Actualiza el estilo del botón activo en el sidebar
        
        Args:
            modulo_activo (str): Nombre del módulo actualmente activo
        """
        for nombre_modulo, btn_frame in self.nav_buttons.items():
            if nombre_modulo == modulo_activo:
                # Botón activo: azul más claro
                btn_frame.config(bg='#2a5fa0')
                for child in btn_frame.winfo_children():
                    child.config(bg='#2a5fa0')
            else:
                # Botones inactivos: azul oscuro
                btn_frame.config(bg='#12345f')
                for child in btn_frame.winfo_children():
                    child.config(bg='#12345f')
    
    def _on_close(self):
        """Maneja el cierre de la ventana"""
        try:
            print("🔄 Cerrando aplicación...")
            
            # Limpiar recursos de los módulos
            if hasattr(self, 'ocupabilidad'):
                self.ocupabilidad.limpiar_recursos()
            if hasattr(self, 'ventas'):
                self.ventas.limpiar_recursos()
            
            # Destruir ventana
            self.root.destroy()
            print("✅ Aplicación cerrada correctamente")
            
        except Exception as e:
            print(f"⚠️ Error al cerrar: {e}")
            self.root.destroy()