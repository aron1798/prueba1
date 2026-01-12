# modules/ocupabilidad/processor.py
from datetime import datetime

class CursoProcessor:
    """Procesador de datos de cursos - Aplica transformaciones y cálculos"""
    
    def __init__(self, data_manager):
        """
        Inicializa el procesador de cursos
        
        Args:
            data_manager: Instancia de DataManager para acceso a configuraciones
        """
        self.data_manager = data_manager
        
        # Columnas a mostrar - ORDEN FINAL
        self.columnas = [
            'programa_frecuencia', 'fch_inicio', 'Avance_Proyectado', 'dias_para_inicio',
            'Inscritos_Mes', 'Inscritos_Totales', 'Inscritos_Retirados', 
            'Inscritos_Activos', 'Inscritos_PC', 'Meta_Curso', 'Avance_Inscritos'
        ]

    def obtener_datos_procesados(self, ano, mes):
        """Obtiene y procesa todos los datos para el dashboard"""
        try:
            # Cargar datos de matrículas del mes seleccionado (Conteo simple)
            datos_matriculas = self.data_manager.cargar_datos_matriculas(ano, mes)
            
            # --- Cargar datos DETALLADOS para filtrar P.C. correctamente ---
            datos_raw_matriculas = self.data_manager.ejecutar_consulta_matriculados_detalle(ano, mes)
            
            # Obtener datos originales de la BD (Cursos del periodo)
            datos_originales = self.data_manager.ejecutar_consulta_cursos(ano, mes)
            
            # Aplicar personalizaciones y procesamiento
            datos_procesados = self.aplicar_personalizaciones(datos_originales, datos_matriculas, datos_raw_matriculas)
            
            return datos_procesados
            
        except Exception as e:
            print(f"❌ Error obteniendo datos procesados: {e}")
            return []

    def aplicar_personalizaciones(self, datos_originales, datos_matriculas, datos_raw_matriculas):
        """Aplica las personalizaciones del JSON a los datos y filtra por flg_activo"""
        print("🎯 Aplicando personalizaciones...")
        
        if 'cursos_personalizados' not in self.data_manager.config_data:
            datos_filtrados = [curso for curso in datos_originales if curso.get('flg_activo', '') != 'NO']
        else:
            cursos_personalizados = self.data_manager.config_data['cursos_personalizados']
            datos_filtrados = []
            
            for curso in datos_originales:
                num_indice = str(curso.get('num_indice', ''))
                
                if num_indice in cursos_personalizados:
                    personalizacion = cursos_personalizados[num_indice]
                    
                    if 'fch_inicio' in personalizacion:
                        curso['fch_inicio'] = personalizacion['fch_inicio']
                    if 'flg_activo' in personalizacion:
                        curso['flg_activo'] = personalizacion['flg_activo']
                    if 'dsc_programa' in personalizacion:
                        curso['dsc_programa'] = personalizacion['dsc_programa']
                    if 'dsc_det_programa' in personalizacion:
                        curso['dsc_det_programa'] = personalizacion['dsc_det_programa']
                
                if curso.get('flg_activo', '') != 'NO':
                    datos_filtrados.append(curso)
        
        print(f"📊 Cursos después de filtrado: {len(datos_filtrados)}")
        
        # Aplicar reemplazos de programas
        datos_filtrados = self.aplicar_reemplazos_programas(datos_filtrados)
        
        # Concatenar PROGRAMA y FRECUENCIA
        datos_filtrados = self.concatenar_programa_frecuencia(datos_filtrados)
        
        # Formatear fechas
        for curso in datos_filtrados:
            if 'fch_inicio' in curso:
                curso['fch_inicio'] = self.formatear_fecha(curso['fch_inicio'])
        
        # Calcular días para inicio
        datos_filtrados = self.calcular_dias_para_inicio_cursos(datos_filtrados)
        
        # Agregar INSCRITOS_MES
        datos_filtrados = self.agregar_inscritos_mes(datos_filtrados, datos_matriculas)
        
        # Agregar INSCRITOS_PC (Con lógica corregida: SOLO Mat + C1 + Estado)
        datos_filtrados = self.agregar_inscritos_pc(datos_filtrados, datos_raw_matriculas)
        
        # Agregar META_CURSO
        datos_filtrados = self.agregar_meta_curso(datos_filtrados)
        
        # Agregar AVANCE_PROYECTADO
        datos_filtrados = self.agregar_avance_proyectado(datos_filtrados)
        
        # Agregar AVANCE_INSCRITOS
        datos_filtrados = self.agregar_avance_inscritos(datos_filtrados)
        
        return datos_filtrados

    def aplicar_reemplazos_programas(self, datos):
        """Aplica los reemplazos de nombres de programas"""
        print("🔄 Aplicando reemplazos de programas...")
        
        if 'reemplazos_programas' in self.data_manager.replace_data:
            reemplazos = self.data_manager.replace_data['reemplazos_programas']
            print(f"📋 Reemplazos disponibles: {len(reemplazos)}")
            
            reemplazos_aplicados = 0
            for curso in datos:
                programa_original = curso.get('dsc_programa', '')
                if programa_original in reemplazos:
                    nuevo_nombre = reemplazos[programa_original]
                    print(f"🔄 Reemplazando: '{programa_original}' → '{nuevo_nombre}'")
                    curso['dsc_programa'] = nuevo_nombre
                    reemplazos_aplicados += 1
            
            print(f"✅ Total reemplazos aplicados: {reemplazos_aplicados}")
        else:
            print("❌ No se encontró 'reemplazos_programas' en el JSON")
        
        return datos

    def concatenar_programa_frecuencia(self, datos):
        """Concatena PROGRAMA y FRECUENCIA en una sola columna"""
        print("🔗 Concatenando PROGRAMA y FRECUENCIA...")
        
        for curso in datos:
            programa = curso.get('dsc_programa', '')
            frecuencia = curso.get('cod_frecuencia', '')
            
            # Crear la nueva columna concatenada
            if programa and frecuencia:
                curso['programa_frecuencia'] = f"{programa} - {frecuencia}"
            elif programa:
                curso['programa_frecuencia'] = programa
            elif frecuencia:
                curso['programa_frecuencia'] = frecuencia
            else:
                curso['programa_frecuencia'] = ""
        
        return datos

    def formatear_fecha(self, fecha_str):
        """Convierte fecha de YYYY-MM-DD HH:MM:SS.sss a DD-MM-YYYY"""
        try:
            if not fecha_str:
                return ""
            
            if isinstance(fecha_str, str) and len(fecha_str) == 10 and fecha_str[2] == '-' and fecha_str[5] == '-':
                return fecha_str
            
            if '.' in str(fecha_str):
                fecha_obj = datetime.strptime(str(fecha_str), '%Y-%m-%d %H:%M:%S.%f')
            else:
                fecha_obj = datetime.strptime(str(fecha_str), '%Y-%m-%d %H:%M:%S')
            
            return fecha_obj.strftime('%d-%m-%Y')
        except (ValueError, TypeError) as e:
            print(f"Error formateando fecha '{fecha_str}': {e}")
            return str(fecha_str)

    def calcular_dias_para_inicio(self, fecha_str, cod_estado):
        """Calcula los días faltantes para el inicio del curso"""
        try:
            # Si el estado es SUS, retornar "SUSPENDIDO"
            if cod_estado == 'SUS':
                return "SUSPENDIDO"
            
            if not fecha_str:
                return ""
            
            # Convertir fecha string a objeto datetime
            if isinstance(fecha_str, str) and len(fecha_str) == 10 and fecha_str[2] == '-' and fecha_str[5] == '-':
                # Formato DD-MM-YYYY
                fecha_curso = datetime.strptime(fecha_str, '%d-%m-%Y')
            else:
                # Otros formatos, intentar convertir
                fecha_curso = datetime.strptime(str(fecha_str), '%Y-%m-%d %H:%M:%S')
            
            # Fecha actual (sin hora, solo fecha)
            hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_curso = fecha_curso.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calcular diferencia en días
            diferencia = (fecha_curso - hoy).days
            
            if diferencia < 0:
                return "INICIADO"
            elif diferencia == 0:
                return "0"
            else:
                return str(diferencia)
                
        except (ValueError, TypeError) as e:
            print(f"Error calculando días para inicio '{fecha_str}': {e}")
            return ""

    def calcular_dias_para_inicio_cursos(self, datos):
        """Calcula los días para inicio de todos los cursos"""
        print("📅 Calculando días para inicio...")
        
        for curso in datos:
            fecha_inicio = curso.get('fch_inicio', '')
            cod_estado = curso.get('cod_estado', '')
            curso['dias_para_inicio'] = self.calcular_dias_para_inicio(fecha_inicio, cod_estado)
        
        return datos

    def agregar_inscritos_mes(self, datos, datos_matriculas):
        """Agrega la columna INSCRITOS_MES basada en los datos de matrículas del mes"""
        print("📈 Agregando INSCRITOS_MES...")
        
        dict_norm = {str(k): v for k, v in datos_matriculas.items()}
        
        inscritos_mes_total = 0
        for curso in datos:
            num_indice = str(curso.get('num_indice', ''))
            if num_indice in dict_norm:
                curso['Inscritos_Mes'] = dict_norm[num_indice]
                inscritos_mes_total += dict_norm[num_indice]
            else:
                curso['Inscritos_Mes'] = 0
        
        print(f"✅ Total inscritos del mes: {inscritos_mes_total}")
        return datos

    def agregar_inscritos_pc(self, datos, datos_raw_matriculas):
        """
        Agrega la columna INSCRITOS_PC.
        REGLAS:
        1. Estado: 'ALU' o 'PRE'
        2. Saldo Matrícula: 0
        3. Saldo Cuota 1: 0
        (Se ignora saldo de cuota 2 en adelante)
        """
        print("\n" + "="*60)
        print("🕵️ DEBUG INSCRITOS P.C. (Lógica: Solo Matrícula y C1 pagadas)")
        print("="*60)
        
        stats = {
            'total_leidos': 0,
            'rechazo_estado': 0,    # No es ALU ni PRE
            'rechazo_deuda_ini': 0, # Debe Matrícula o Cuota 1
            'aceptados': 0
        }
        
        conteo_pc = {}

        if datos_raw_matriculas:
            for m in datos_raw_matriculas:
                try:
                    stats['total_leidos'] += 1
                    
                    estado = str(m.get('estado_matricula', '')).strip()
                    num_indice = str(m.get('num_indice', ''))
                    
                    # Convertimos a float (usamos < 1 para ignorar centimos)
                    saldo_mat = float(m.get('imp_saldo_matricula', 0) or 0)
                    saldo_c1 = float(m.get('imp_saldo_cuota1', 0) or 0)
                    
                    # --- REGLAS DE FILTRADO ---
                    
                    # 1. ¿Es Estado Valido?
                    if estado not in ['ALU', 'PRE']:
                        stats['rechazo_estado'] += 1
                        continue 
                        
                    # 2. ¿Pagó Matrícula y Cuota 1?
                    if not ((saldo_mat < 1) and (saldo_c1 < 1)):
                        stats['rechazo_deuda_ini'] += 1
                        continue
                    
                    # SI PASA, LO CONTAMOS (Ya no miramos la Cuota 2)
                    conteo_pc[num_indice] = conteo_pc.get(num_indice, 0) + 1
                    stats['aceptados'] += 1

                except Exception:
                    continue
        
        # Imprimir reporte en consola
        print(f"📊 RESUMEN DEBUG:")
        print(f"   ➤ Total alumnos procesados: {stats['total_leidos']}")
        print(f"   ❌ Rechazados por ESTADO (No ALU/PRE): {stats['rechazo_estado']}")
        print(f"   ❌ Rechazados por DEUDA (Deben Matrícula o C1): {stats['rechazo_deuda_ini']}")
        print(f"   ✅ TOTAL ACEPTADOS: {stats['aceptados']}")
        print("="*60 + "\n")

        # Asignar valores
        inscritos_pc_total = 0
        for curso in datos:
            num_indice = str(curso.get('num_indice', ''))
            valor = conteo_pc.get(num_indice, 0)
            curso['Inscritos_PC'] = valor
            inscritos_pc_total += valor
        
        return datos

    def calcular_meta_curso(self, nombre_programa, cod_estado):
        """Calcula la meta del curso basado en los patrones del JSON y estado"""
        try:
            # Si el estado es SUS, retornar 0 inmediatamente
            if cod_estado == 'SUS':
                print(f"⏸️ Curso suspendido: '{nombre_programa}' → META = 0")
                return 0
            
            nombre_programa_upper = nombre_programa.upper()
            clasificaciones = self.data_manager.meta_data.get('clasificacion_programas', {})
            
            # Buscar en orden de prioridad
            for categoria, config in clasificaciones.items():
                patrones = config.get('patrones', [])
                for patron in patrones:
                    if patron.upper() in nombre_programa_upper:
                        valor = config.get('valor', 0)
                        print(f"🎯 Meta encontrada: '{nombre_programa}' → {categoria} → {valor}")
                        return valor
            
            # Si no encuentra coincidencia, usar valor por defecto
            valor_default = self.data_manager.meta_data.get('clasificacion_default', {}).get('valor', 15)
            print(f"⚡ Meta por defecto: '{nombre_programa}' → {valor_default}")
            return valor_default
            
        except Exception as e:
            print(f"❌ Error calculando meta para '{nombre_programa}': {e}")
            return 0

    def agregar_meta_curso(self, datos):
        """Agrega la columna META_CURSO basada en la clasificación y estado"""
        print("🎯 Calculando META_CURSO...")
        
        for curso in datos:
            nombre_programa = curso.get('dsc_programa', '')
            cod_estado = curso.get('cod_estado', '')
            curso['Meta_Curso'] = self.calcular_meta_curso(nombre_programa, cod_estado)
        
        return datos

    def determinar_categoria_programa(self, nombre_programa):
        """Determina la categoría del programa basado en los patrones del JSON"""
        try:
            nombre_programa_upper = nombre_programa.upper()
            clasificaciones = self.data_manager.meta_data.get('clasificacion_programas', {})
            
            # Buscar en orden de prioridad
            for categoria, config in clasificaciones.items():
                patrones = config.get('patrones', [])
                for patron in patrones:
                    if patron.upper() in nombre_programa_upper:
                        print(f"🎯 Categoría encontrada: '{nombre_programa}' → {categoria}")
                        return categoria
            
            # Si no encuentra coincidencia, usar categoría por defecto
            categoria_default = self.data_manager.meta_data.get('clasificacion_default', {}).get('categoria', 'SEMINARIOS')
            print(f"⚡ Categoría por defecto: '{nombre_programa}' → {categoria_default}")
            return categoria_default
            
        except Exception as e:
            print(f"❌ Error determinando categoría para '{nombre_programa}': {e}")
            return "SEMINARIOS"

    def calcular_avance_proyectado(self, nombre_programa, dias_para_inicio):
        """Calcula el avance proyectado basado en categoría y días para inicio"""
        try:
            # Si está suspendido, retornar 0
            if dias_para_inicio == "SUSPENDIDO":
                print(f"⏸️ Curso suspendido: '{nombre_programa}' → AVANCE = 0")
                return 0
            
            # Determinar categoría del programa
            categoria = self.determinar_categoria_programa(nombre_programa)
            
            # Determinar días a buscar
            if dias_para_inicio == "INICIADO":
                dias_buscar = 1000
            else:
                try:
                    dias_buscar = int(dias_para_inicio)
                except ValueError:
                    print(f"⚠️ Días para inicio inválido: '{dias_para_inicio}' → AVANCE = 0")
                    return 0
            
            # Buscar en los pronósticos
            pronosticos = self.data_manager.pronostico_data.get('pronosticos', [])
            for pronostico in pronosticos:
                if (pronostico.get('TipoPrograma') == categoria and 
                    pronostico.get('Dias') == dias_buscar):
                    valor = pronostico.get('Pronostico', 0)
                    print(f"📈 Avance proyectado: '{nombre_programa}' → {categoria}, {dias_buscar}d → {valor}")
                    return valor
            
            # Si no encuentra coincidencia exacta
            print(f"🔍 No se encontró pronóstico exacto para {categoria}, {dias_buscar}d")
            return 0
            
        except Exception as e:
            print(f"❌ Error calculando avance proyectado para '{nombre_programa}': {e}")
            return 0

    def agregar_avance_proyectado(self, datos):
        """Agrega la columna AVANCE_PROYECTADO basada en categoría y días para inicio"""
        print("📊 Calculando AVANCE_PROYECTADO...")
        
        for curso in datos:
            nombre_programa = curso.get('dsc_programa', '')
            dias_para_inicio = curso.get('dias_para_inicio', '')
            curso['Avance_Proyectado'] = self.calcular_avance_proyectado(nombre_programa, dias_para_inicio)
        
        return datos

    def calcular_avance_inscritos(self, inscritos_activos, meta_curso):
        """Calcula el porcentaje de avance de inscritos"""
        try:
            if meta_curso > 0:
                porcentaje = (inscritos_activos / meta_curso) * 100
                return f"{porcentaje:.1f}%"
            else:
                return "0%"
        except (TypeError, ZeroDivisionError):
            return "0%"

    def agregar_avance_inscritos(self, datos):
        """Agrega la columna AVANCE_INSCRITOS basada en activos vs meta"""
        print("📊 Calculando AVANCE_INSCRITOS...")
        
        for curso in datos:
            inscritos_activos = curso.get('Inscritos_Activos', 0)
            meta_curso = curso.get('Meta_Curso', 0)
            curso['Avance_Inscritos'] = self.calcular_avance_inscritos(inscritos_activos, meta_curso)
        
        return datos