from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

class PDFReport(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'INFORME DE DIÁLISIS PERITONEAL', 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 6, 'Paciente: Mónica Danitza Rojas Rocha - DNI: 93.620.268', 0, 1, 'C')
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_informe_pdf(registros, estadisticas, fecha_inicio, fecha_fin, tipo_informe):
    """Genera PDF con informe completo del período seleccionado"""
    
    pdf = PDFReport()
    
    if tipo_informe == 'base':
        pdf = PDFReport(orientation='L')  # Horizontal para base de datos
    
    pdf.add_page()
    
    # ============================================================
    # ENCABEZADO DEL INFORME
    # ============================================================
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Período: {fecha_inicio} al {fecha_fin}', 0, 1)
    pdf.cell(0, 8, f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(5)
    
    # ============================================================
    # INFORME RESUMEN (si aplica)
    # ============================================================
    if tipo_informe in ['resumen', 'completo'] and estadisticas:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'RESUMEN ESTADÍSTICO DEL PERÍODO', 0, 1)
        pdf.ln(2)
        
        # Estadísticas generales
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, '📊 Datos Generales:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'   • Días con tratamiento: {estadisticas.get("total_dias", 0)}', 0, 1)
        pdf.cell(0, 6, f'   • Total de registros: {estadisticas.get("total_registros", 0)}', 0, 1)
        pdf.cell(0, 6, f'   • Registros manuales: {estadisticas.get("total_manuales", 0)}', 0, 1)
        pdf.cell(0, 6, f'   • Registros cicladora: {estadisticas.get("total_cicladoras", 0)}', 0, 1)
        pdf.ln(3)
        
        # Análisis de UF
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, '💧 Análisis de Ultrafiltración (UF):', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'   • UF Total del período: {estadisticas.get("uf_total_periodo", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   • UF Promedio por día: {estadisticas.get("uf_promedio_dia", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   • Valor máximo: {estadisticas.get("uf_max", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   • Valor mínimo: {estadisticas.get("uf_min", 0):.0f} ml', 0, 1)
        pdf.ln(3)
        
        # Alertas clínicas
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, '⚠️ Alertas Clínicas:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        dias_negativos = estadisticas.get("dias_con_uf_negativa", 0)
        if dias_negativos > 0:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 6, f'   • Días con UF negativa: {dias_negativos} (retención de líquidos)', 0, 1)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 6, f'   • Días con UF negativa: 0 (✓ Sin retención)', 0, 1)
        
        pdf.cell(0, 6, f'   • Días con UF positiva: {estadisticas.get("dias_con_uf_positiva", 0)}', 0, 1)
        pdf.ln(5)
        
        # Tabla de resumen diario (si hay datos)
        if estadisticas.get('dias') and len(estadisticas['dias']) > 0:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, '📅 Resumen por Día:', 0, 1)
            pdf.ln(2)
            
            # Encabezados
            pdf.set_font('Arial', 'B', 9)
            col_widths = [30, 25, 25, 25, 25]
            headers = ['Fecha', 'UF Cici', 'Manuales', 'UF Manual', 'UF Total']
            
            for header in headers:
                pdf.cell(col_widths[headers.index(header)], 7, header, 1, 0, 'C')
            pdf.ln()
            
            # Datos
            pdf.set_font('Arial', '', 8)
            for fecha, datos_dia in estadisticas['dias'].items():
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                fecha_str = fecha_obj.strftime('%d/%m')
                
                pdf.cell(col_widths[0], 6, fecha_str, 1, 0, 'C')
                pdf.cell(col_widths[1], 6, f'{datos_dia.get("uf_cicladora", 0):.0f}', 1, 0, 'R')
                pdf.cell(col_widths[2], 6, f'{datos_dia.get("num_manuales", 0)}', 1, 0, 'C')
                pdf.cell(col_widths[3], 6, f'{datos_dia.get("uf_manual", 0):.0f}', 1, 0, 'R')
                
                total_uf = datos_dia.get("uf_cicladora", 0) + datos_dia.get("uf_manual", 0)
                if total_uf < 0:
                    pdf.set_text_color(255, 0, 0)
                pdf.cell(col_widths[4], 6, f'{total_uf:.0f}', 1, 0, 'R')
                pdf.set_text_color(0, 0, 0)
                pdf.ln()
            pdf.ln(10)
    
    # ============================================================
    # BASE DE DATOS (registros detallados)
    # ============================================================
    if tipo_informe in ['base', 'completo'] and registros:
        if tipo_informe == 'completo':
            pdf.add_page()
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'DETALLE DE REGISTROS', 0, 1)
        pdf.ln(5)
        
        # Encabezados de tabla
        pdf.set_font('Arial', 'B', 8)
        headers = ['ID', 'Fecha', 'Hora', 'Tipo', 'UF (ml)', 'Color', 'Obs']
        col_widths = [10, 20, 15, 18, 20, 18, 35]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
        pdf.ln()
        
        # Datos
        pdf.set_font('Arial', '', 7)
        for reg in registros[:50]:  # Limitar a 50 registros
            pdf.cell(col_widths[0], 5, str(reg.get('id', '')), 1, 0, 'C')
            
            fecha = reg.get('fecha', '')[-5:] if reg.get('fecha') else ''
            pdf.cell(col_widths[1], 5, fecha, 1, 0, 'C')
            
            hora = reg.get('hora', '')[:5] if reg.get('hora') else ''
            pdf.cell(col_widths[2], 5, hora, 1, 0, 'C')
            
            tipo = reg.get('tipo_dialisis', '')[:3] if reg.get('tipo_dialisis') else ''
            pdf.cell(col_widths[3], 5, tipo, 1, 0, 'C')
            
            # UF según tipo
            if reg.get('tipo_dialisis') == 'Cicladora':
                uf = reg.get('uf_total_cicladora_ml', 0)
            else:
                uf = reg.get('uf_recambio_manual_ml', 0)
            
            if uf:
                if uf < 0:
                    pdf.set_text_color(255, 0, 0)
                pdf.cell(col_widths[4], 5, f'{uf:.0f}', 1, 0, 'R')
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.cell(col_widths[4], 5, '-', 1, 0, 'C')
            
            color = reg.get('color_bolsa', '')[:3] if reg.get('color_bolsa') else '-'
            pdf.cell(col_widths[5], 5, color, 1, 0, 'C')
            
            obs = reg.get('observaciones', '')[:20]
            if len(reg.get('observaciones', '')) > 20:
                obs += '...'
            pdf.cell(col_widths[6], 5, obs, 1, 0, 'L')
            pdf.ln()
    
    # Guardar PDF
    filename = f"informe_dialisis_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
    pdf.output(filename)
    return filename
