import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

BAIRES_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "https://dhroamdwktzvurhgiwgi.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRocm9hbWR3a3R6dnVyaGdpd2dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxNDYwMTEsImV4cCI6MjA4ODcyMjAxMX0.Nzh55cT8EwETHDeJSt3D1CSGplVyO75XuqhyTPQ3-Ig")
        self.supabase: Client = create_client(self.url, self.key)
    
    def get_configuracion(self):
        response = self.supabase.table('configuracion').select('*').order('id', desc=True).limit(1).execute()
        if response.data:
            config = response.data[0]
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
        data = {
            'peso_kg': peso,
            'altura_m': altura,
            'ultima_actualizacion': datetime.now(BAIRES_TZ).isoformat()
        }
        response = self.supabase.table('configuracion').update(data).eq('id', 1).execute()
        return response.data
    
    def get_ultimo_registro(self):
        response = self.supabase.table('ultimo_registro').select('*').execute()
        return response.data[0] if response.data else None
    
    def get_ultimo_registro_manual(self):
        response = self.supabase.table('registros_manual')\
            .select('*')\
            .order('fecha', desc=True)\
            .order('hora', desc=True)\
            .limit(1)\
            .execute()
        return response.data[0] if response.data else None
    
    def insert_registro_manual(self, datos):
        ahora = datetime.now(BAIRES_TZ)
        
        # Obtener último registro manual para calcular balance
        ultimo = self.get_ultimo_registro_manual()
        
        # Calcular balance: Drenaje actual - Infusión anterior
        if ultimo:
            volumen_infusion_anterior = ultimo.get('volumen_infundido_ml', 0)
            balance = round((datos['peso_drenaje'] * 1000) - volumen_infusion_anterior)
        else:
            balance = 0
        
        registro = {
            'fecha': datos.get('fecha', ahora.date().isoformat()),
            'hora': datos.get('hora', ahora.time().strftime('%H:%M:%S')),
            'concentracion': datos['concentracion'],
            'peso_bolsa_llena_kg': datos['peso_llena'],
            'peso_bolsa_vacia_kg': datos.get('peso_vacia', 0),
            'peso_bolsa_drenaje_kg': datos['peso_drenaje'],
            'balance_ml': balance,
            'observaciones': datos.get('observaciones', '')
        }
        
        response = self.supabase.table('registros_manual').insert(registro).execute()
        return response.data
    
    def insert_registro_cicladora(self, datos):
        ahora = datetime.now(BAIRES_TZ)
        
        registro = {
            'fecha': datos.get('fecha', ahora.date().isoformat()),
            'hora_inicio': datos.get('hora_inicio', ahora.time().strftime('%H:%M:%S')),
            'hora_fin': datos.get('hora_fin', (ahora + timedelta(hours=8)).time().strftime('%H:%M:%S')),
            'vol_drenaje_inicial_ml': datos.get('drenaje_inicial'),
            'uf_total_cicladora_ml': datos.get('uf_total'),
            'tiempo_permanencia_promedio_min': datos.get('tiempo_permanencia'),
            'tiempo_perdido_min': datos.get('tiempo_perdido'),
            'vol_total_solucion_ml': datos.get('volumen_solucion'),
            'numero_ciclos_completados': datos.get('num_ciclos'),
            'observaciones': datos.get('observaciones', '')
        }
        
        response = self.supabase.table('registros_cicladora').insert(registro).execute()
        return response.data
    
    def get_registros_fecha(self, fecha_inicio, fecha_fin):
        """Obtener todos los registros en rango de fechas (usando vista unificada)"""
        response = self.supabase.table('registros_unificado')\
            .select('*')\
            .gte('fecha', fecha_inicio)\
            .lte('fecha', fecha_fin)\
            .order('fecha', desc=True)\
            .execute()
        return response.data
    
    def get_estadisticas_periodo(self, fecha_inicio, fecha_fin):
        """Calcular estadísticas completas"""
        registros = self.get_registros_fecha(fecha_inicio, fecha_fin)
        
        if not registros:
            return None
        
        # Agrupar por día manualmente (sin pandas)
        dias = {}
        for reg in registros:
            fecha = reg['fecha']
            if fecha not in dias:
                dias[fecha] = {
                    'uf_cicladora': 0,
                    'uf_manual': 0,
                    'num_manuales': 0,
                    'num_cicladoras': 0
                }
            
            if reg['tipo_dialisis'] == 'Cicladora':
                dias[fecha]['uf_cicladora'] += reg.get('uf_total_cicladora_ml', 0) or 0
                dias[fecha]['num_cicladoras'] += 1
            else:
                dias[fecha]['uf_manual'] += reg.get('uf_recambio_manual_ml', 0) or 0
                dias[fecha]['num_manuales'] += 1
        
        # Calcular totales por día
        uf_por_dia = []
        fechas_lista = []
        for fecha, datos in dias.items():
            total_uf = (datos['uf_cicladora'] or 0) + (datos['uf_manual'] or 0)
            uf_por_dia.append(total_uf)
            fechas_lista.append(fecha)
        
        return {
            'total_dias': len(dias),
            'total_registros': len(registros),
            'total_manuales': sum(d['num_manuales'] for d in dias.values()),
            'total_cicladoras': sum(d['num_cicladoras'] for d in dias.values()),
            'uf_total_periodo': sum(uf_por_dia),
            'uf_promedio_dia': sum(uf_por_dia) / len(dias) if dias else 0,
            'dias_con_uf_negativa': sum(1 for uf in uf_por_dia if uf < 0),
            'dias_con_uf_positiva': sum(1 for uf in uf_por_dia if uf > 0),
            'uf_max': max(uf_por_dia) if uf_por_dia else 0,
            'uf_min': min(uf_por_dia) if uf_por_dia else 0,
            'dias': dias,
            'uf_por_dia': uf_por_dia,
            'fechas': fechas_lista
        }
    def eliminar_registro(self, registro_id, tipo):
        """Eliminar un registro por ID y tipo"""
        try:
            tabla = 'registros_manual' if tipo == 'Manual' else 'registros_cicladora'
            response = self.supabase.table(tabla).delete().eq('id', registro_id).execute()
            return response.data
        except Exception as e:
            print(f"Error eliminando registro: {e}")
            return None
