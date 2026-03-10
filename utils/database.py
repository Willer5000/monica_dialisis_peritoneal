import os
from supabase import create_client, Client
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

BAIRES_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "https://dhroamdwktzvurhgiwgi.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRocm9hbWR3a3R6dnVyaGdpd2dpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxNDYwMTEsImV4cCI6MjA4ODcyMjAxMX0.Nzh55cT8EwETHDeJSt3D1CSGplVyO75XuqhyTPQ3-Ig")
        self.supabase: Client = create_client(self.url, self.key)
    
    def get_configuracion(self):
        """Obtener configuración del paciente"""
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
        """Actualizar peso y altura"""
        data = {
            'peso_kg': peso,
            'altura_m': altura,
            'ultima_actualizacion': datetime.now(BAIRES_TZ).isoformat()
        }
        response = self.supabase.table('configuracion').update(data).eq('id', 1).execute()
        return response.data
    
    def get_ultimo_registro(self):
        """Obtener el último registro (cualquier tipo)"""
        response = self.supabase.table('ultimo_registro').select('*').execute()
        return response.data[0] if response.data else None
    
    def get_ultimo_registro_manual(self):
        """Obtener el último registro manual (para calcular balance)"""
        response = self.supabase.table('registros_manual')\
            .select('*')\
            .order('fecha', desc=True)\
            .order('hora', desc=True)\
            .limit(1)\
            .execute()
        return response.data[0] if response.data else None
    
    def insert_registro_manual(self, datos):
        """Insertar registro manual con cálculo de balance"""
        ahora = datetime.now(BAIRES_TZ)
        
        # Obtener último registro manual para calcular balance
        ultimo = self.get_ultimo_registro_manual()
        
        # Calcular balance: Drenaje actual - Infusión anterior
        if ultimo:
            # Usar volumen infundido del último registro como referencia
            volumen_infusion_anterior = ultimo.get('volumen_infundido_ml', 0)
            balance = (datos['peso_drenaje'] * 1000) - volumen_infusion_anterior
        else:
            # Primer registro del día, balance = 0
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
        """Insertar registro de cicladora"""
        ahora = datetime.now(BAIRES_TZ)
        
        registro = {
            'fecha': datos.get('fecha', ahora.date().isoformat()),
            'hora_inicio': datos.get('hora_inicio', ahora.time().strftime('%H:%M:%S')),
            'hora_fin': datos.get('hora_fin', (ahora + timedelta(hours=8)).time().strftime('%H:%M:%S')),
            'volumen_drenaje_inicial_ml': datos.get('drenaje_inicial'),
            'ultrafiltracion_total_ml': datos.get('uf_total'),
            'tiempo_permanencia_promedio_min': datos.get('tiempo_permanencia'),
            'tiempo_perdido_min': datos.get('tiempo_perdido'),
            'volumen_total_solucion_ml': datos.get('volumen_solucion'),
            'numero_ciclos_completados': datos.get('num_ciclos'),
            'observaciones': datos.get('observaciones', '')
        }
        
        response = self.supabase.table('registros_cicladora').insert(registro).execute()
        return response.data
    
    def get_registros_manual(self, fecha_inicio, fecha_fin):
        """Obtener registros manuales en rango de fechas"""
        response = self.supabase.table('registros_manual')\
            .select('*')\
            .gte('fecha', fecha_inicio)\
            .lte('fecha', fecha_fin)\
            .order('fecha')\
            .order('hora')\
            .execute()
        return response.data
    
    def get_registros_cicladora(self, fecha_inicio, fecha_fin):
        """Obtener registros de cicladora en rango de fechas"""
        response = self.supabase.table('registros_cicladora')\
            .select('*')\
            .gte('fecha', fecha_inicio)\
            .lte('fecha', fecha_fin)\
            .order('fecha')\
            .execute()
        return response.data
    
    def get_estadisticas_periodo(self, fecha_inicio, fecha_fin):
        """Calcular estadísticas completas para el período"""
        manuales = self.get_registros_manual(fecha_inicio, fecha_fin)
        cicladoras = self.get_registros_cicladora(fecha_inicio, fecha_fin)
        
        # Análisis de manuales
        balances_manual = [r['balance_ml'] for r in manuales if r['balance_ml']]
        
        # Análisis de cicladoras
        ufs_cicladora = [r['ultrafiltracion_total_ml'] for r in cicladoras if r['ultrafiltracion_total_ml']]
        eficiencias = [r['eficiencia_ml_por_hora'] for r in cicladoras if r['eficiencia_ml_por_hora']]
        
        return {
            'total_manuales': len(manuales),
            'total_cicladoras': len(cicladoras),
            'balances_manual': balances_manual,
            'ufs_cicladora': ufs_cicladora,
            'eficiencias': eficiencias,
            'promedio_balance_manual': sum(balances_manual) / len(balances_manual) if balances_manual else 0,
            'promedio_uf_cicladora': sum(ufs_cicladora) / len(ufs_cicladora) if ufs_cicladora else 0,
            'total_uf_periodo': sum(ufs_cicladora) + sum(balances_manual),
            'dias_con_balance_negativo': sum(1 for b in balances_manual if b < 0),
            'dias_con_uf_negativa': sum(1 for u in ufs_cicladora if u < 0),
        }
