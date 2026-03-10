import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

# Configuración de zona horaria Buenos Aires
BAIRES_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "https://dhroamdwktzvurhgiwgi.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "sb_publishable_hUDOyddHWnA4by2njU9pOg_dOzD59fM")
        self.supabase: Client = create_client(self.url, self.key)
    
    def get_configuracion(self):
        """Obtener configuración del paciente con edad calculada"""
        response = self.supabase.table('configuracion').select('*').order('id', desc=True).limit(1).execute()
        if response.data:
            config = response.data[0]
            # Calcular edad desde Python
            from datetime import date
            nacimiento = datetime.strptime(config['fecha_nacimiento'], '%Y-%m-%d').date()
            hoy = date.today()
            edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
            config['edad'] = edad
            return config
        return {
            'nombre': 'Mónica Danitza Rojas Rocha',
            'dni': '93620268',
            'peso_kg': 65.0,
            'altura_m': 1.55,
            'edad': 38
        }
    
    def update_configuracion(self, peso, altura):
        """Actualizar peso y altura"""
        data = {
            'peso_kg': peso,
            'altura_m': altura,
            'ultima_actualizacion': datetime.now(BAIRES_TZ).isoformat()
        }
        response = self.supabase.table('configuracion').update(data).eq('id', 1).execute()
        return response.data
    
    def get_ultimo_registro(self):
        """Obtener el último registro con análisis de tendencia"""
        response = self.supabase.table('registros')\
            .select('*')\
            .order('fecha', desc=True)\
            .order('hora', desc=True)\
            .limit(5)\
            .execute()
        
        if not response.data:
            return None
        
        registros = response.data
        ultimo = registros[0]
        
        # Calcular UF a mostrar según tipo
        if ultimo['tipo_dialisis'] == 'Manual':
            ultimo['uf_mostrar'] = float(ultimo['uf_recambio_manual_ml'] or 0)
        else:
            ultimo['uf_mostrar'] = float(ultimo['uf_total_cicladora_ml'] or 0)
        
        # Calcular tendencia (comparar con promedio de últimos 3)
        if len(registros) >= 2:
            ufs_anteriores = []
            for r in registros[1:4]:  # Hasta 3 anteriores
                if r['tipo_dialisis'] == 'Manual':
                    ufs_anteriores.append(float(r['uf_recambio_manual_ml'] or 0))
                else:
                    ufs_anteriores.append(float(r['uf_total_cicladora_ml'] or 0))
            
            if ufs_anteriores:
                promedio_anterior = sum(ufs_anteriores) / len(ufs_anteriores)
                ultimo['tendencia'] = ultimo['uf_mostrar'] - promedio_anterior
                ultimo['tendencia_porcentaje'] = (ultimo['tendencia'] / promedio_anterior * 100) if promedio_anterior != 0 else 0
        else:
            ultimo['tendencia'] = 0
            ultimo['tendencia_porcentaje'] = 0
        
        return ultimo
    
    def insert_registro(self, datos):
        """Insertar un nuevo registro con cálculo correcto de UF manual"""
        ahora = datetime.now(BAIRES_TZ)
        
        # Obtener el último registro manual anterior para calcular UF correctamente
        if datos['tipo'] == 'Manual':
            # Buscar el último registro manual para conocer la infusión anterior
            response_anterior = self.supabase.table('registros')\
                .select('*')\
                .eq('tipo_dialisis', 'Manual')\
                .order('fecha', desc=True)\
                .order('hora', desc=True)\
                .limit(1)\
                .execute()
            
            peso_sol_actual = float(datos['peso_solucion'])
            peso_dren_actual = float(datos['peso_drenaje'])
            
            # Si hay un registro anterior, usamos su peso de solución como referencia
            if response_anterior.data:
                registro_anterior = response_anterior.data[0]
                peso_sol_anterior = float(registro_anterior['peso_bolsa_solucion_kg'] or 0)
                
                # Cálculo correcto: DRENAJE ACTUAL - INFUSIÓN ANTERIOR
                uf_manual = (peso_dren_actual - peso_sol_anterior) * 1000
                
                # Guardamos también el método de cálculo para referencia
                metodo_calculo = f"dren_actual({peso_dren_actual}kg) - sol_anterior({peso_sol_anterior}kg)"
            else:
                # Si es el primer registro, usamos la solución actual como referencia
                uf_manual = (peso_dren_actual - peso_sol_actual) * 1000
                metodo_calculo = f"primer_registro: dren_actual - sol_actual"
            
            registro = {
                'fecha': datos.get('fecha', ahora.date().isoformat()),
                'hora': datos.get('hora', ahora.time().strftime('%H:%M:%S')),
                'tipo_dialisis': 'Manual',
                'observaciones': f"{datos.get('observaciones', '')} | Cálculo UF: {metodo_calculo}",
                'color_bolsa': datos['color_bolsa'],
                'peso_bolsa_solucion_kg': peso_sol_actual,
                'peso_bolsa_drenaje_kg': peso_dren_actual,
                'uf_recambio_manual_ml': uf_manual
            }
        else:  # Cicladora
            registro = {
                'fecha': datos.get('fecha', ahora.date().isoformat()),
                'hora': datos.get('hora', ahora.time().strftime('%H:%M:%S')),
                'tipo_dialisis': 'Cicladora',
                'observaciones': datos.get('observaciones', ''),
                'uf_total_cicladora_ml': int(datos.get('uf_cicladora', 0))
            }
        
        response = self.supabase.table('registros').insert(registro).execute()
        
        # Actualizar totales del día
        self.actualizar_totales_diarios(registro['fecha'])
        
        return response.data
    
    def actualizar_totales_diarios(self, fecha):
        """Recalcular UF total y número de recambios para una fecha"""
        response = self.supabase.table('registros')\
            .select('*')\
            .eq('fecha', fecha)\
            .execute()
        
        if not response.data:
            return
        
        registros = response.data
        total_uf = 0
        num_manuales = 0
        
        for reg in registros:
            if reg['tipo_dialisis'] == 'Cicladora':
                total_uf += reg.get('uf_total_cicladora_ml', 0)
            else:
                total_uf += reg.get('uf_recambio_manual_ml', 0)
                num_manuales += 1
        
        # Actualizar todos los registros del día
        for reg in registros:
            self.supabase.table('registros')\
                .update({
                    'uf_total_dia_ml': total_uf,
                    'num_recambios_manuales_dia': num_manuales
                })\
                .eq('id', reg['id'])\
                .execute()
    
    def get_registros_fecha(self, fecha_inicio, fecha_fin):
        """Obtener registros en un rango de fechas"""
        response = self.supabase.table('registros')\
            .select('*')\
            .gte('fecha', fecha_inicio)\
            .lte('fecha', fecha_fin)\
            .order('fecha', desc=True)\
            .order('hora', desc=True)\
            .execute()
        return response.data
    
    def get_estadisticas_periodo(self, fecha_inicio, fecha_fin):
        """Obtener estadísticas para el informe"""
        response = self.supabase.table('registros')\
            .select('*')\
            .gte('fecha', fecha_inicio)\
            .lte('fecha', fecha_fin)\
            .order('fecha')\
            .execute()
        
        registros = response.data
        if not registros:
            return None
        
        # Agrupar por fecha
        dias = {}
        uf_por_dia = []
        
        for reg in registros:
            fecha = reg['fecha']
            if fecha not in dias:
                dias[fecha] = {
                    'uf_cicladora': 0,
                    'uf_manual': 0,
                    'num_manuales': 0,
                    'total_uf': 0
                }
            
            if reg['tipo_dialisis'] == 'Cicladora':
                dias[fecha]['uf_cicladora'] += reg.get('uf_total_cicladora_ml', 0)
            else:
                dias[fecha]['uf_manual'] += reg.get('uf_recambio_manual_ml', 0)
                dias[fecha]['num_manuales'] += 1
        
        # Calcular totales por día
        for fecha, datos in dias.items():
            datos['total_uf'] = datos['uf_cicladora'] + datos['uf_manual']
            uf_por_dia.append(datos['total_uf'])
        
        # Calcular estadísticas
        uf_cicladora_total = sum(d['uf_cicladora'] for d in dias.values())
        uf_manual_total = sum(d['uf_manual'] for d in dias.values())
        total_uf_periodo = sum(uf_por_dia)
        
        # Análisis de tendencia
        uf_ordenadas = uf_por_dia
        tendencia = "estable"
        if len(uf_ordenadas) >= 3:
            if uf_ordenadas[-1] > uf_ordenadas[-2] > uf_ordenadas[-3]:
                tendencia = "creciente"
            elif uf_ordenadas[-1] < uf_ordenadas[-2] < uf_ordenadas[-3]:
                tendencia = "decreciente"
        
        return {
            'total_dias': len(dias),
            'total_registros': len(registros),
            'total_recambios_manuales': sum(d['num_manuales'] for d in dias.values()),
            'uf_total_periodo': total_uf_periodo,
            'uf_promedio_dia': total_uf_periodo / len(dias) if dias else 0,
            'uf_cicladora_total': uf_cicladora_total,
            'uf_manual_total': uf_manual_total,
            'dias_con_uf_negativa': sum(1 for uf in uf_por_dia if uf < 0),
            'dias_con_uf_positiva': sum(1 for uf in uf_por_dia if uf > 0),
            'uf_max': max(uf_por_dia) if uf_por_dia else 0,
            'uf_min': min(uf_por_dia) if uf_por_dia else 0,
            'tendencia': tendencia,
            'dias': dias,
            'uf_por_dia': uf_por_dia,
            'fechas': list(dias.keys())
        }
