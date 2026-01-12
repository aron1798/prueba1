# modules/ocupabilidad/view.py
import re
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime # Importamos datetime por si acaso

# Intento de importar tksheet
try:
    import tksheet
    HAS_TKSHEET = True
except Exception:
    HAS_TKSHEET = False

# Importar lógica y procesamiento del mismo módulo
from .logic import AnalizadorCursos

def make_styled_combobox(parent, label_text, textvar, values, width=16):
    """
    Crea un widget compuesto: un card con borde, label y un ttk.Combobox estilizado.
    Retorna (wrapper_frame, combobox_widget).
    """
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass

    style.configure('Blue.TCombobox',
                    fieldbackground='#ffffff',
                    background='#ffffff',
                    foreground='#12345f',
                    padding=6,
                    font=('Arial', 12))

    try:
        style.map('Blue.TCombobox',
                  fieldbackground=[('readonly', '#ffffff'),
                                    ('focus', '#e6f7ff'),
                                    ('!focus', '#ffffff')],
                  background=[('active', '#dfeeff'), ('!active', '#ffffff')])
    except Exception:
        pass

    wrapper = tk.Frame(parent, bg='#d0e7ff', bd=2, relief='solid')
    inner = tk.Frame(wrapper, bg='#ffffff')
    inner.pack(fill='both', expand=True, padx=4, pady=4)

    lbl = tk.Label(inner, text=label_text, bg='#ffffff', fg='#12345f', font=('Arial', 11, 'bold'))
    lbl.pack(anchor='w', padx=6, pady=(2,4))

    cb = ttk.Combobox(inner, textvariable=textvar, values=values,
                      state='readonly', width=width, style='Blue.TCombobox')
    cb.pack(padx=6, pady=(0,6))

    def on_enter(e):
        wrapper.config(bg='#a8d0ff')
    def on_leave(e):
        wrapper.config(bg='#d0e7ff')

    wrapper.bind('<Enter>', on_enter)
    wrapper.bind('<Leave>', on_leave)
    inner.bind('<Enter>', on_enter)
    inner.bind('<Leave>', on_leave)
    lbl.bind('<Enter>', on_enter)
    lbl.bind('<Leave>', on_leave)
    cb.bind('<Enter>', on_enter)
    cb.bind('<Leave>', on_leave)

    return wrapper, cb


class OcupabilidadModule:
    """Módulo de Ocupabilidad - Vista y gestión de datos de cursos"""
    
    def __init__(self, parent_container, data_manager):
        """
        Inicializa el módulo de Ocupabilidad
        """
        self.parent_container = parent_container
        self.data_manager = data_manager
        
        # Inicializar analizador
        self.analizador = AnalizadorCursos(self.data_manager)
        
        # --- MAPA DE MESES PARA TRADUCCIÓN (NUEVO) ---
        self.MAPA_MESES = {
            "ENERO": "1", "FEBRERO": "2", "MARZO": "3", "ABRIL": "4",
            "MAYO": "5", "JUNIO": "6", "JULIO": "7", "AGOSTO": "8",
            "SEPTIEMBRE": "9", "OCTUBRE": "10", "NOVIEMBRE": "11", "DICIEMBRE": "12"
        }
        # Mapa inverso para obtener el nombre a partir del número actual
        self.MAPA_NUMEROS = {v: k for k, v in self.MAPA_MESES.items()}

        # Establecer valores iniciales
        mes_actual_num = str(self._get_current_month())
        nombre_mes_inicial = self.MAPA_NUMEROS.get(mes_actual_num, "ENERO")

        self.mes_seleccionado = tk.StringVar(value=nombre_mes_inicial)
        self.ano_seleccionado = tk.StringVar(value=str(self._get_current_year()))
        
        self.datos = []
        
        # Variable para controlar el ciclo de actualización
        self.timer_id = None
        
        # Frame principal del módulo
        self.main_frame = tk.Frame(parent_container, bg='#e9f0f8')
        
        # Referencias a widgets
        self.sheet = None
        self.filters_frame = None
        self.center_panel = None
        self.lbl_registros = None # Añadida referencia para etiqueta de conteo
        
        # Construir interfaz
        self._build_interface()
        
        # Cargar datos iniciales después de un pequeño delay
        self.main_frame.after(800, self.cargar_datos)
        
        # INICIAR AUTO-REFRESH
        self._iniciar_auto_refresh()
        
        print("✅ Módulo Ocupabilidad inicializado (Meses con Texto)")
    
    def _get_current_month(self):
        """Obtiene el mes actual"""
        try:
            return self.data_manager.get_current_month()
        except Exception:
            return datetime.datetime.now().month
    
    def _get_current_year(self):
        """Obtiene el año actual"""
        try:
            return self.data_manager.get_current_year()
        except Exception:
            return datetime.datetime.now().year

    # -----------------------------------------------------------
    # LÓGICA DE AUTO-ACTUALIZACIÓN
    # -----------------------------------------------------------
    def _iniciar_auto_refresh(self):
        try:
            if self.timer_id:
                try:
                    self.main_frame.after_cancel(self.timer_id)
                except:
                    pass

            config = self.data_manager.config_data.get("config_general", {})
            minutos = config.get("auto_update_minutos", 2) 
            
            ms = int(minutos * 60 * 1000)
            self.timer_id = self.main_frame.after(ms, self._ciclo_refresh)

        except Exception as e:
            print(f"⚠️ Error iniciando auto-refresh (Ocupabilidad): {e}")

    def _ciclo_refresh(self):
        if self.main_frame.winfo_ismapped():
            print("🔄 AUTO-UPDATE: Actualizando Ocupabilidad...")
            self.cargar_datos()
        
        self._iniciar_auto_refresh()
    # -----------------------------------------------------------
    
    def _build_interface(self):
        """Construye toda la interfaz del módulo"""
        # Header
        header = tk.Frame(self.main_frame, bg='#e9f0f8')
        header.pack(fill=tk.X, pady=(0, 10))
        title = tk.Label(header, text="📊 DASHBOARD - OCUPABILIDAD", bg='#e9f0f8',
                         fg='#12345f', font=('Arial', 18, 'bold'))
        title.pack(side=tk.LEFT)
        
        # Filtros
        self._build_filters()
        
        # Área tabla
        self._build_table_area()
    
    def _build_filters(self):
        """Construye la sección de filtros"""
        self.filters_frame = tk.Frame(self.main_frame, bg='#e9f0f8')
        self.filters_frame.pack(fill=tk.X, pady=(10, 10))
        
        # ---------------------------------------------------------------------
        # CAMBIO: LISTA MANUAL DE AÑOS
        # ---------------------------------------------------------------------
        LISTA_ANOS = [2025, 2026]
        anos = [str(y) for y in LISTA_ANOS]
        
        wrapper_year, ano_cb = make_styled_combobox(
            self.filters_frame, "📅 AÑO", self.ano_seleccionado, anos, width=18
        )
        wrapper_year.pack(side=tk.LEFT, padx=(0, 12))
        ano_cb.bind('<<ComboboxSelected>>', lambda e: self.cargar_datos())
        
        # ---------------------------------------------------------------------
        # CAMBIO: MESES CON TEXTO
        # ---------------------------------------------------------------------
        nombres_meses = list(self.MAPA_MESES.keys()) # ["ENERO", "FEBRERO", ...]

        wrapper_month, mes_cb = make_styled_combobox(
            self.filters_frame, "📋 MES", self.mes_seleccionado, nombres_meses, width=12
        )
        wrapper_month.pack(side=tk.LEFT, padx=(0, 12))
        mes_cb.bind('<<ComboboxSelected>>', lambda e: self.cargar_datos())
        
        # Botón Exportar
        export_btn = tk.Button(self.filters_frame, text="💾 EXPORTAR", bg='#4a86e8', fg='white',
                               command=self.exportar_excel, padx=12, pady=8, relief='flat', cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(10,0))
    
    def _build_table_area(self):
        """Construye el área de la tabla"""
        self.center_panel = tk.Frame(self.main_frame, bg='#dfeaf7', bd=0, relief='flat')
        self.center_panel.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Título
        title_frame = tk.Frame(self.center_panel, bg='#dfeaf7')
        title_frame.pack(fill=tk.X, pady=(12, 8), padx=12)
        tk.Label(title_frame, text="Resultados", bg='#dfeaf7', fg='#12345f',
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Contenedor tabla
        table_container = tk.Frame(self.center_panel, bg='#e6eefc', bd=0)
        table_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,12))
        
        if not HAS_TKSHEET:
            warning = tk.Label(table_container, 
                             text="tksheet no está instalado. Instala 'tksheet' para ver la tabla aquí.",
                             bg='#e6eefc', fg='#12345f', font=('Arial', 11))
            warning.pack(padx=20, pady=20)
            self.sheet = None
            return
        
        # Headers de la tabla
        headers = [
            'PROGRAMA', 'FECHA INICIO', '       AVANCE    PROYECTADO',
            '      DIAS PARA    INICIO', '   INSCRITOS    MES', '         TOTAL        INSCRITOS',
            'RETIRADOS', 'ACTIVOS', '   INSCRITOS P.C', '          META          INSCRITOS', 'AVANCE INSCRITOS'
        ]
        
        self.sheet = tksheet.Sheet(
            table_container,
            headers=headers,
            header_height=40,
            row_height=28,
            row_index=False,
            show_row_index=False,
            align="center",
            header_align="center",
            theme="light blue",
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            height=600,
            width=1280,
            total_columns=len(headers)
        )
        
        self.sheet.set_options(
            table_font=('Arial', 8, 'normal'),
            header_font=('Arial', 9, 'bold'),
            table_bg="#ffffff",
            header_bg="#12345f",
            header_fg="#ffffff",
            header_grid_bg="#12345f",
            table_grid_fg="#d1e3ff",
            table_fg="#333333",
            table_selected_cells_bg="#e6f2ff",
            scrollbar_bg="#12345f",
            scrollbar_button_bg="#12345f",
            scrollbar_hover_bg="#b5cef8",
            auto_resize_columns=False
        )
        self.sheet.grid(sticky="nsew")
        self.sheet.enable_bindings(
            "single_select", "row_select", "arrowkeys",
            "right_click_popup_menu", "rc_select",
            "copy", "cut", "paste", "delete"
        )
        
        # Configurar anchos inicialmente
        self._configurar_anchos_columnas()
    
    def _configurar_anchos_columnas(self):
        """Fuerza el ancho de las columnas"""
        if not self.sheet:
            return
        anchos = [280, 90, 90, 90, 90, 90, 80, 80, 80, 90, 170]
        for i, ancho in enumerate(anchos):
            try:
                # only_set_if_too_small=False asegura que se respete el ancho
                self.sheet.column_width(column=i, width=ancho, only_set_if_too_small=False)
            except Exception as e:
                print(f"Error ajustando columna {i}: {e}")
    
    def _eliminar_columnas_extra(self):
        """Elimina columnas fantasma extras"""
        if not self.sheet:
            return
        try:
            self.sheet.total_columns(11)
            for col in range(11, 100):
                try:
                    self.sheet.hide_columns(col)
                except:
                    break
            self.sheet.set_options(
                show_x_scrollbar=False,
                auto_resize_columns=False,
                expand_sheet_if_paste_too_big=False
            )
            self.sheet.refresh()
        except Exception as e:
            print(f"Error eliminando columnas extra: {e}")
    
    def cargar_datos(self):
        """Inicia la carga de datos en un thread separado"""
        thread = threading.Thread(target=self._thread_cargar)
        thread.daemon = True
        thread.start()
    
    def _thread_cargar(self):
        """Thread que carga los datos de la BD"""
        try:
            ano = self.ano_seleccionado.get()
            nombre_mes = self.mes_seleccionado.get()
            
            # --- TRADUCCIÓN: Convertir "ENERO" -> "1" para el Analizador ---
            mes_numero = self.MAPA_MESES.get(nombre_mes, "1")
            
            print(f"📊 Cargando Ocupabilidad: {nombre_mes} ({mes_numero}) / {ano}")
            
            # Obtener datos procesados (Usando el NUMERO del mes)
            datos_raw = self.analizador.obtener_datos_procesados(str(ano), str(mes_numero))
            self.datos = datos_raw or []
            
            # Formatear para tabla
            sheet_data, _ = self.analizador.formatear_datos_para_tabla(self.datos)
            
            # Actualizar UI en el thread principal
            self.main_frame.after(0, lambda: self._actualizar_sheet(sheet_data))
            
        except Exception as e:
            self.main_frame.after(0, lambda: messagebox.showerror("Error", f"Error cargando datos: {e}"))
    
    def _extract_percentage(self, text):
        """
        Extrae un número decimal representando el porcentaje desde una cadena
        """
        if text is None:
            return 0.0
        s = str(text)
        m = re.search(r'([0-9]+(?:\.[0-9]+)?)', s)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return 0.0
        return 0.0
    
    def _actualizar_sheet(self, sheet_data):
        """Actualiza la tabla con los datos"""
        if not HAS_TKSHEET or not self.sheet:
            return
        try:
            # Limpiar colores previos
            try:
                self.sheet.dehighlight_all()
            except Exception:
                pass
            
            # Establecer datos
            self.sheet.set_sheet_data(sheet_data)
            
            # Identificar última fila (TOTAL GENERAL)
            ultima_fila_idx = len(sheet_data) - 1
            
            # Colorear filas
            for row_idx in range(len(sheet_data)):
                if row_idx == ultima_fila_idx:
                    # TOTAL GENERAL: azul claro en todas las columnas
                    for col in range(11):
                        self.sheet.highlight_cells(
                            row=row_idx, 
                            column=col, 
                            bg="#e6f2ff",
                            fg="#12345f",
                            redraw=False
                        )
                else:
                    # FILAS NORMALES: colorear columna 10 según porcentaje
                    raw_val = sheet_data[row_idx][10] if len(sheet_data[row_idx]) > 10 else ""
                    porcentaje = self._extract_percentage(raw_val)
                    
                    # COLORES SEGÚN PORCENTAJE
                    if porcentaje < 60:
                        bg, fg = "#ffe6e6", "#cc0000"  # ROJO
                    elif porcentaje < 80:
                        bg, fg = "#fff2cc", "#b36b00"  # NARANJA
                    else:
                        bg, fg = "#e6f7e6", "#2d862d"  # VERDE
                    
                    self.sheet.highlight_cells(
                        row=row_idx, 
                        column=10, 
                        bg=bg, 
                        fg=fg, 
                        redraw=False
                    )
            
            # Forzar anchos después de X milisegundos
            self.main_frame.after(10, self._configurar_anchos_columnas)
            self.main_frame.after(20, self._eliminar_columnas_extra)
            
            # Refrescar
            try:
                self.sheet.refresh()
            except Exception:
                pass
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la tabla: {e}")
    
    def exportar_excel(self):
        """Exporta los datos a Excel"""
        if not self.datos:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        try:
            # MANTENEMOS TU LÓGICA ORIGINAL AQUÍ
            # Convertimos el nombre del mes a número para el nombre del archivo
            nombre_mes = self.mes_seleccionado.get()
            mes_num = self.MAPA_MESES.get(nombre_mes, "0")
            
            archivo = self.analizador.exportar_a_excel(
                self.datos, 
                self.ano_seleccionado.get(), 
                mes_num # Pasamos el número del mes para que lo use el nombre del archivo
            )
            messagebox.showinfo("Éxito", f"Datos exportados a {archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")
    
    def mostrar(self):
        """Muestra este módulo"""
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        print("👁️ Módulo Ocupabilidad mostrado")
    
    def ocultar(self):
        """Oculta este módulo"""
        self.main_frame.pack_forget()
        print("🙈 Módulo Ocupabilidad ocultado")
    
    def limpiar_recursos(self):
        """Limpia recursos antes de destruir el módulo"""
        if self.timer_id:
            try:
                self.main_frame.after_cancel(self.timer_id)
            except:
                pass
        self.datos = []
        if self.sheet:
            try:
                self.sheet.destroy()
            except:
                pass
        print("🧹 Recursos de Ocupabilidad limpiados")