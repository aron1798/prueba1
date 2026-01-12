# modules/ventas.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import pandas as pd
import datetime

try:
    import tksheet
    HAS_TKSHEET = True
except Exception:
    HAS_TKSHEET = False

def make_styled_combobox(parent, label_text, textvar, values, width=16):
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


class VentasModule:
    def __init__(self, parent_container, data_manager):
        self.parent_container = parent_container
        self.data_manager = data_manager
        
        # --- MAPA DE MESES PARA TRADUCCIÓN ---
        self.MAPA_MESES = {
            "ENERO": "1", "FEBRERO": "2", "MARZO": "3", "ABRIL": "4",
            "MAYO": "5", "JUNIO": "6", "JULIO": "7", "AGOSTO": "8",
            "SEPTIEMBRE": "9", "OCTUBRE": "10", "NOVIEMBRE": "11", "DICIEMBRE": "12"
        }
        # Mapa inverso para obtener el nombre a partir del número actual
        self.MAPA_NUMEROS = {v: k for k, v in self.MAPA_MESES.items()}
        
        # Establecer valores iniciales (Nombre del mes actual)
        mes_actual_num = str(self._get_current_month_num())
        nombre_mes_inicial = self.MAPA_NUMEROS.get(mes_actual_num, "ENERO")
        
        self.mes_seleccionado = tk.StringVar(value=nombre_mes_inicial)
        self.ano_seleccionado = tk.StringVar(value=str(self._get_current_year()))
        
        self.datos = []
        self.timer_id = None
        
        self.main_frame = tk.Frame(parent_container, bg='#e9f0f8')
        
        self.sheet = None
        self.filters_frame = None
        self.center_panel = None
        self.total_label = None
        
        self._build_interface()
        
        self.main_frame.after(800, self.cargar_datos)
        self._iniciar_auto_refresh()
        
        print("✅ Módulo Ventas inicializado (Meses con Texto)")
    
    def _get_current_month_num(self):
        try:
            return self.data_manager.get_current_month()
        except Exception:
            return datetime.datetime.now().month
    
    def _get_current_year(self):
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
            print(f"⚠️ Error iniciando auto-refresh: {e}")

    def _ciclo_refresh(self):
        if self.main_frame.winfo_ismapped():
            print("🔄 AUTO-UPDATE: Actualizando datos de Ventas...")
            self.cargar_datos()
        self._iniciar_auto_refresh()
    # -----------------------------------------------------------
    
    def _build_interface(self):
        header = tk.Frame(self.main_frame, bg='#e9f0f8')
        header.pack(fill=tk.X, pady=(0, 10))
        title = tk.Label(header, text="💼 DASHBOARD - VENTAS", bg='#e9f0f8',
                        fg='#12345f', font=('Arial', 18, 'bold'))
        title.pack(side=tk.LEFT)
        
        self._build_filters()
        self._build_table_area()
    
    def _build_filters(self):
        self.filters_frame = tk.Frame(self.main_frame, bg='#e9f0f8')
        self.filters_frame.pack(fill=tk.X, pady=(10, 10))
        
        # --- LISTA MANUAL DE AÑOS ---
        LISTA_ANOS = [2025, 2026] 
        anos_str = [str(y) for y in LISTA_ANOS]
        
        wrapper_year, ano_cb = make_styled_combobox(
            self.filters_frame, "📅 AÑO", self.ano_seleccionado, anos_str, width=18
        )
        wrapper_year.pack(side=tk.LEFT, padx=(0, 12))
        ano_cb.bind('<<ComboboxSelected>>', lambda e: self.cargar_datos())
        
        # --- MESES CON TEXTO ---
        nombres_meses = list(self.MAPA_MESES.keys()) # ["ENERO", "FEBRERO", ...]
        
        wrapper_month, mes_cb = make_styled_combobox(
            self.filters_frame, "📋 MES", self.mes_seleccionado, nombres_meses, width=12
        )
        wrapper_month.pack(side=tk.LEFT, padx=(0, 12))
        mes_cb.bind('<<ComboboxSelected>>', lambda e: self.cargar_datos())
        
        export_btn = tk.Button(self.filters_frame, text="💾 EXPORTAR", bg='#4a86e8', fg='white',
                               command=self.exportar_excel, padx=12, pady=8, relief='flat', cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(10,0))
    
    def _build_table_area(self):
        self.center_panel = tk.Frame(self.main_frame, bg='#dfeaf7', bd=0, relief='flat')
        self.center_panel.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        title_frame = tk.Frame(self.center_panel, bg='#dfeaf7')
        title_frame.pack(fill=tk.X, pady=(12, 8), padx=12)
        
        tk.Label(title_frame, text="Ventas por Vendedor (ALU/PRE)", bg='#dfeaf7', fg='#12345f',
                font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        self.total_label = tk.Label(title_frame, text="Total: S/ 0.00", bg='#dfeaf7', 
                                    fg='#2d862d', font=('Arial', 12, 'bold'))
        self.total_label.pack(side=tk.RIGHT, padx=20)
        
        table_container = tk.Frame(self.center_panel, bg='#e6eefc', bd=0)
        table_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,12))
        
        if not HAS_TKSHEET:
            warning = tk.Label(table_container, 
                             text="tksheet no está instalado.",
                             bg='#e6eefc', fg='#12345f', font=('Arial', 11))
            warning.pack(padx=20, pady=20)
            self.sheet = None
            return
        
        headers = [
            'VENDEDOR', 'INSCRITOS', 'VENTA INSCRITOS', 
            'INSCRITOS P.C', 'VENTA P.C', 'INSCRITOS PEND.', 
            'VENTA PEND.', 'AVANCE P.C TOTAL'
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
            table_font=('Arial', 10, 'normal'),
            header_font=('Arial', 11, 'bold'),
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
        
        self._configurar_anchos_columnas()
    
    def _configurar_anchos_columnas(self):
        if not self.sheet:
            return
        anchos = [270, 90, 180, 90, 155, 90, 155, 200]
        for i, ancho in enumerate(anchos):
            try:
                self.sheet.column_width(column=i, width=ancho, only_set_if_too_small=False)
            except Exception as e:
                print(f"Error ajustando columna {i}: {e}")
    
    def cargar_datos(self):
        thread = threading.Thread(target=self._thread_cargar)
        thread.daemon = True
        thread.start()
    
    def _thread_cargar(self):
        try:
            ano = self.ano_seleccionado.get()
            nombre_mes = self.mes_seleccionado.get()
            
            # --- TRADUCCIÓN: Convertir "ENERO" -> "1" para la Base de Datos ---
            mes_numero = self.MAPA_MESES.get(nombre_mes, "1")
            
            print(f"💼 Cargando Ventas: {nombre_mes} ({mes_numero}) / {ano}")
            
            # Llamar a la BD con el NÚMERO
            datos_raw = self.data_manager.ejecutar_consulta_ventas(str(ano), str(mes_numero))
            self.datos = datos_raw or []
            
            sheet_data = self._formatear_datos_para_tabla(self.datos)
            
            self.main_frame.after(0, lambda: self._actualizar_sheet(sheet_data))
            
        except Exception as e:
            error_msg = f"Error cargando datos de ventas: {e}"
            print(f"❌ {error_msg}")
            self.main_frame.after(0, lambda: messagebox.showerror("Error", error_msg))
    
    def _formatear_datos_para_tabla(self, datos):
        if not datos:
            return []
        
        sheet_data = []
        total_monto = 0.0
        total_cantidad = 0
        total_pc = 0.0
        total_cantidad_pc = 0
        total_pendientes = 0.0
        total_cantidad_pendientes = 0
        total_avance_pc_total = 0.0
        
        for registro in datos:
            vendedor = registro.get('VENDEDOR', 'SIN VENDEDOR')
            monto = registro.get('MONTO', 0.0)
            cantidad = registro.get('CANTIDAD', 0)
            ventas_pc = registro.get('VENTAS_PC', 0.0)
            cantidad_pc = registro.get('INSCRITOS_PC', 0)
            pendientes = registro.get('PENDIENTES', 0.0)
            cant_pendientes = registro.get('INSCRITOS_PENDIENTES', 0)
            
            avance_pc_total = ventas_pc + pendientes
            
            total_monto += monto
            total_cantidad += cantidad
            total_pc += ventas_pc
            total_cantidad_pc += cantidad_pc
            total_pendientes += pendientes
            total_cantidad_pendientes += cant_pendientes
            total_avance_pc_total += avance_pc_total
            
            monto_fmt = f"S/ {monto:,.2f}"
            pc_fmt = f"S/ {ventas_pc:,.2f}"
            pendientes_fmt = f"S/ {pendientes:,.2f}"
            avance_total_fmt = f"S/ {avance_pc_total:,.2f}"
            
            sheet_data.append([
                vendedor, cantidad, monto_fmt, cantidad_pc, pc_fmt, 
                cant_pendientes, pendientes_fmt, avance_total_fmt
            ])
        
        total_monto_fmt = f"S/ {total_monto:,.2f}"
        total_pc_fmt = f"S/ {total_pc:,.2f}"
        total_pend_fmt = f"S/ {total_pendientes:,.2f}"
        total_avance_fmt = f"S/ {total_avance_pc_total:,.2f}"
        
        sheet_data.append([
            "TOTAL GENERAL", total_cantidad, total_monto_fmt, 
            total_cantidad_pc, total_pc_fmt, total_cantidad_pendientes, 
            total_pend_fmt, total_avance_fmt
        ])
        
        return sheet_data
    
    def _actualizar_sheet(self, sheet_data):
        if not HAS_TKSHEET or not self.sheet:
            return
        
        try:
            try:
                self.sheet.dehighlight_all()
            except Exception:
                pass
            
            self.sheet.set_sheet_data(sheet_data)
            self._configurar_anchos_columnas()
            
            ultima_fila_idx = len(sheet_data) - 1
            if ultima_fila_idx >= 0:
                for col in range(8):
                    self.sheet.highlight_cells(
                        row=ultima_fila_idx, 
                        column=col, 
                        bg="#e6f2ff",
                        fg="#12345f",
                        redraw=False
                    )
            
            if sheet_data and ultima_fila_idx >= 0:
                total_texto = sheet_data[ultima_fila_idx][2]
                self.total_label.config(text=f"Total: {total_texto}")
            
            try:
                self.sheet.refresh()
            except Exception:
                pass
            
            print(f"✅ Tabla actualizada: {len(sheet_data)-1} vendedores")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la tabla: {e}")
    
    def exportar_excel(self):
        if not self.datos:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        try:
            import pandas as pd
            datos_export = []
            for d in self.datos:
                nuevo_d = d.copy()
                nuevo_d['AVANCE_PC_TOTAL'] = d.get('VENTAS_PC', 0) + d.get('PENDIENTES', 0)
                datos_export.append(nuevo_d)
                
            df = pd.DataFrame(datos_export)
            
            ano = self.ano_seleccionado.get()
            mes = self.mes_seleccionado.get()
            archivo = f"ventas_{ano}_{mes}.xlsx"
            
            df.to_excel(archivo, index=False)
            messagebox.showinfo("Éxito", f"Datos exportados a {archivo}")
            
        except ImportError:
            messagebox.showerror("Error", "Instala 'pandas' y 'openpyxl'.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")
    
    def mostrar(self):
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        print("👁️ Módulo Ventas mostrado")
    
    def ocultar(self):
        self.main_frame.pack_forget()
        print("🙈 Módulo Ventas ocultado")
    
    def limpiar_recursos(self):
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
        print("🧹 Recursos de Ventas limpiados")