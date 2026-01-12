# modules/ocupabilidad/logic.py
import pandas as pd
from .processor import CursoProcessor

class AnalizadorCursos:
    """Analizador de cursos - Lógica de cálculo y estadísticas"""
    
    def __init__(self, data_manager):
        """
        Inicializa el analizador de cursos
        
        Args:
            data_manager: Instancia de DataManager para acceso a datos
        """
        self.data_manager = data_manager
        self.curso_processor = CursoProcessor(self.data_manager)
        self.columnas = self.curso_processor.columnas

    def get_current_month(self):
        """Obtiene el mes actual"""
        return self.data_manager.get_current_month()

    def get_current_year(self):
        """Obtiene el año actual"""
        return self.data_manager.get_current_year()

    def actualizar_configuracion(self):
        """Actualiza la configuración del sistema"""
        print("🔄 Actualización automática de configuración...")
        self.data_manager.cargar_toda_configuracion()

    def obtener_datos_procesados(self, ano, mes):
        """Obtiene datos procesados para el año y mes especificados"""
        return self.curso_processor.obtener_datos_procesados(ano, mes)

    def formatear_datos_para_tabla(self, datos):
        """Formatea los datos para mostrar en la tabla"""
        if not datos:
            return [], {}

        sheet_data = []
        totales = {
            'avance': 0, 'mes': 0, 'totales': 0,
            'retirados': 0, 'activos': 0, 'pc': 0, 'meta': 0
        }
        
        for registro in datos:
            fila = []
            for col in self.columnas:
                if col != 'Avance_Inscritos':
                    valor = registro.get(col, '')
                    fila.append(str(valor))
                    
                    # Acumular totales
                    self._acumular_totales(totales, col, registro)
                else:
                    porcentaje = self.calcular_porcentaje_avance(
                        registro.get('Inscritos_Activos', 0),
                        registro.get('Meta_Curso', 0)
                    )
                    fila.append(self.crear_barra_texto_color(porcentaje))
            
            sheet_data.append(fila)
        
        # Agregar fila de totales
        fila_totales = self.crear_fila_totales(totales)
        sheet_data.append(fila_totales)
        
        return sheet_data, totales

    def _acumular_totales(self, totales, col, registro):
        """Acumula valores para los totales"""
        if col == 'Avance_Proyectado':
            totales['avance'] += registro.get(col, 0)
        elif col == 'Inscritos_Mes':
            totales['mes'] += registro.get(col, 0)
        elif col == 'Inscritos_Totales':
            totales['totales'] += registro.get(col, 0)
        elif col == 'Inscritos_Retirados':
            totales['retirados'] += registro.get(col, 0)
        elif col == 'Inscritos_Activos':
            totales['activos'] += registro.get(col, 0)
        elif col == 'Inscritos_PC':
            totales['pc'] += registro.get(col, 0)
        elif col == 'Meta_Curso':
            totales['meta'] += registro.get(col, 0)

    def crear_fila_totales(self, totales):
        """Crea la fila de totales"""
        porcentaje = self.calcular_porcentaje_avance(totales['activos'], totales['meta'])
        return [
            "TOTAL GENERAL", "", str(int(totales['avance'])), "",
            str(totales['mes']), str(totales['totales']), 
            str(totales['retirados']), str(totales['activos']),
            str(totales['pc']), str(totales['meta']), self.crear_barra_texto_color(porcentaje)
        ]

    def calcular_porcentaje_avance(self, activos, meta):
        """Calcula el porcentaje de avance"""
        return (activos / meta * 100) if meta > 0 else 0

    def crear_barra_texto_color(self, porcentaje):
        """Crea barra de progreso textual"""
        longitud = 10
        llenas = int((min(porcentaje, 100) / 100) * longitud)
        vacias = longitud - llenas
        
        barra = '█' * llenas + '░' * vacias
        porc_text = f"{porcentaje:.1f}%"
        espacios = " " * (6 - len(porc_text))
        
        return f"{porc_text}{espacios}{barra}"

    def get_intervalo_actualizacion(self):
        """Obtiene el intervalo de actualización automática"""
        return self.data_manager.config_data.get(
            'config_general', {}
        ).get('auto_update_minutos', 5) * 60000

    def exportar_a_excel(self, datos, ano, mes):
        """Exporta datos a Excel"""
        df = pd.DataFrame(datos)
        df_exportar = df[self.columnas]
        archivo = f"cursos_{ano}_{mes}.xlsx"
        df_exportar.to_excel(archivo, index=False)
        return archivo

    # Métodos adicionales para análisis estadístico
    def calcular_metricas_generales(self, datos):
        """Calcula métricas generales del sistema"""
        if not datos:
            return {}
        
        df = pd.DataFrame(datos)
        
        metricas = {
            'total_cursos': len(datos),
            'total_inscritos': df['Inscritos_Activos'].sum(),
            'total_meta': df['Meta_Curso'].sum(),
            'porcentaje_avance_general': (df['Inscritos_Activos'].sum() / df['Meta_Curso'].sum() * 100) if df['Meta_Curso'].sum() > 0 else 0,
            'cursos_sobre_meta': len(df[df['Inscritos_Activos'] >= df['Meta_Curso']]),
            'cursos_bajo_meta': len(df[df['Inscritos_Activos'] < df['Meta_Curso']]),
            'tasa_retiro': (df['Inscritos_Retirados'].sum() / df['Inscritos_Totales'].sum() * 100) if df['Inscritos_Totales'].sum() > 0 else 0,
            'total_inscritos_pc': df['Inscritos_PC'].sum()
        }
        
        return metricas

    def obtener_top_programas(self, datos, top_n=5):
        """Obtiene los top programas por rendimiento"""
        if not datos:
            return []
        
        df = pd.DataFrame(datos)
        df['Porcentaje_Avance'] = df.apply(
            lambda x: self.calcular_porcentaje_avance(x['Inscritos_Activos'], x['Meta_Curso']), 
            axis=1
        )
        
        top_programas = df.nlargest(top_n, 'Porcentaje_Avance')[
            ['programa_frecuencia', 'Inscritos_Activos', 'Meta_Curso', 'Porcentaje_Avance']
        ].to_dict('records')
        
        return top_programas

    def calcular_tendencias_mensuales(self, ano):
        """Calcula tendencias mensuales para un año especifico"""
        tendencias = {}
        
        for mes in range(1, 13):
            try:
                datos_mes = self.obtener_datos_procesados(str(ano), str(mes))
                if datos_mes:
                    metricas = self.calcular_metricas_generales(datos_mes)
                    tendencias[mes] = metricas
            except Exception as e:
                print(f"Error procesando mes {mes}: {e}")
                continue
        
        return tendencias