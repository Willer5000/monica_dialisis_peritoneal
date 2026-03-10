import os
from supabase import create_client, Client
from datetime import datetime
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
        """Obtener configuración del paciente"""
        response = self.supabase.table('configuracion').select('*').order('id', desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    
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
        """Obtener el último registro (útil para frontend)"""
        response = self.supabase.table('ultimo_registro').select('*').execute()
        return response.data[0] if response.data else None
    
    def insert_registro(self, datos):
        """Insertar un nuevo registro"""
        # Asegurar zona horaria Buenos Aires
        ahora = datetime.now(BAIRES_TZ)
        
        registro = {
            'fecha': datos.get('fecha', ahora.date().isoformat()),
            'hora': datos.get('hora', ahora.time().strftime('%H:%M:%S')),
            'tipo_dialisis': datos['tipo'],
            'observaciones': datos.get('observaciones', '')
        }
        
        if datos['tipo'] == 'Manual':
            peso_sol = float(datos['peso_solucion'])
            peso_dren = float(datos['peso_drenaje'])
            uf_manual = (peso_dren - peso_sol) * 1000
            
            registro.update({
                'color_bolsa': datos['color_bolsa'],
                'peso_bolsa_solucion_kg': peso_sol,
                'peso_bolsa_drenaje_kg': peso_dren,
                'uf_recambio_manual_ml': uf_manual
            })
        else:
            registro.update({
                'uf_total_cicladora_ml': int(datos.get('uf_cicladora', 0))
            })
        
        response = self.supabase.table('registros').insert(registro).execute()
        
        # Actualizar totales del día
        self.actualizar_totales_diarios(registro['fecha'])
        
        return response.data
    
    def actualizar_totales_diarios(self, fecha):
        """Recalcular UF total y número de recambios para una fecha"""
        # Obtener todos los registros del día
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
            .execute()
        
        registros = response.data
        if not registros:
            return None
        
        # Agrupar por fecha
        dias = {}
        for reg in registros:
            fecha = reg['fecha']
            if fecha not in dias:
                dias[fecha] = {
                    'uf_cicladora': 0,
                    'uf_manual': 0,
                    'num_manuales': 0
                }
            
            if reg['tipo_dialisis'] == 'Cicladora':
                dias[fecha]['uf_cicladora'] += reg.get('uf_total_cicladora_ml', 0)
            else:
                dias[fecha]['uf_manual'] += reg.get('uf_recambio_manual_ml', 0)
                dias[fecha]['num_manuales'] += 1
        
        # Calcular estadísticas
        uf_por_dia = [d['uf_cicladora'] + d['uf_manual'] for d in dias.values()]
        uf_cicladora_total = sum(d['uf_cicladora'] for d in dias.values())
        uf_manual_total = sum(d['uf_manual'] for d in dias.values())
        
        return {
            'total_dias': len(dias),
            'total_registros': len(registros),
            'total_recambios_manuales': sum(d['num_manuales'] for d in dias.values()),
            'uf_total_periodo': sum(uf_por_dia),
            'uf_promedio_dia': sum(uf_por_dia) / len(dias) if dias else 0,
            'uf_cicladora_total': uf_cicladora_total,
            'uf_manual_total': uf_manual_total,
            'dias_con_uf_negativa': sum(1 for uf in uf_por_dia if uf < 0),
            'dias_con_uf_positiva': sum(1 for uf in uf_por_dia if uf > 0),
            'dias': dias
        }
