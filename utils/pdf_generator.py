from fpdf import FPDF
from datetime import datetime
import os

class PDFReport(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'INFORME DE DIALISIS PERITONEAL', 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 6, 'Paciente: Monica Danitza Rojas Rocha - DNI: 93.620.268', 0, 1, 'C')
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_informe_pdf(registros, estadisticas, fecha_inicio, fecha_fin, tipo_informe):
    """Genera PDF con informe completo del periodo seleccionado"""
    
    pdf = PDFReport()
    
    if tipo_informe == 'base':
        pdf = PDFReport(orientation='L')  # Horizontal para base de datos
    
    pdf.add_page()
    
    # ============================================================
    # ENCABEZADO DEL INFORME
    # ============================================================
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Periodo: {fecha_inicio} al {fecha_fin}', 0, 1)
    pdf.cell(0, 8, f'Fecha de generacion: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(5)
    
    # ============================================================
    # INFORME RESUMEN (si aplica)
    # ============================================================
    if tipo_informe in ['resumen', 'completo'] and estadisticas:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'RESUMEN ESTADISTICO DEL PERIODO', 0, 1)
        pdf.ln(2)
        
        # Estadisticas generales
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, 'Datos Generales:', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'   - Dias con tratamiento: {estadisticas.get("total_dias", 0)}', 0, 1)
        pdf.cell(0, 6, f'   - Total de registros: {estadisticas.get("total_registros", 0)}', 0, 1)
        pdf.cell(0, 6, f'   - Registros manuales: {estadisticas.get("total_manuales", 0)}', 0, 1)
        pdf.cell(0, 6, f'   - Registros cicladora: {estadisticas.get("total_cicladoras", 0)}', 0, 1)
        pdf.ln(3)
        
        # Analisis de UF
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, 'Analisis de Ultrafiltracion (UF):', 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'   - UF Total del periodo: {estadisticas.get("uf_total_periodo", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   - UF Promedio por dia: {estadisticas.get("uf_promedio_dia", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   - Valor maximo: {estadisticas.get("uf_max", 0):.0f} ml', 0, 1)
        pdf.cell(0, 6, f'   - Valor minimo: {estadisticas.get("uf_min", 0):.0f} ml', 0, 1)
        pdf.ln(3)
        
        # Alertas clinicas
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, 'Alertas Clinicas:', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        dias_negativos = estadisticas.get("dias_con_uf_negativa", 0)
        if dias_negativos > 0:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 6, f'   - ATENCION: Dias con UF negativa: {dias_negativos}', 0, 1)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 6, f'   - Dias con UF negativa: 0', 0, 1)
        
        pdf.cell(0, 6, f'   - Dias con UF positiva: {estadisticas.get("dias_con_uf_positiva", 0)}', 0, 1)
        pdf.ln(5)
        
        # Tabla de resumen diario
        if estadisticas.get('dias') and len(estadisticas['dias']) > 0:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, 'Resumen por Dia:', 0, 1)
            pdf.ln(2)
            
            # Encabezados - más anchos
            pdf.set_font('Arial', 'B', 9)
            col_widths = [35, 30, 30, 30, 35]  # Columnas más anchas
            headers = ['Fecha', 'UF Cici', 'Manuales', 'UF Manual', 'UF Total']
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
            pdf.ln()
            
            # Datos
            pdf.set_font('Arial', '', 8)
            for fecha, datos_dia in estadisticas['dias'].items():
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                fecha_str = fecha_obj.strftime('%d/%m/%Y')  # Fecha completa con año
                
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
        
        # Verificar si hay registros manuales para mostrar columnas adicionales
        hay_manuales = any(r['tipo_dialisis'] == 'Manual' for r in registros)
        hay_cicladoras = any(r['tipo_dialisis'] == 'Cicladora' for r in registros)
        
        if hay_manuales:
            # Tabla para registros manuales (con todas las columnas)
            pdf.set_font('Arial', 'B', 8)
            headers = ['ID', 'Fecha', 'Hora', 'Tipo', 'Color', 'Infundido', 'Drenado', 'Balance', 'Obs']
            col_widths = [10, 22, 15, 18, 18, 22, 22, 22, 28]  # Más anchas
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
            pdf.ln()
            
            pdf.set_font('Arial', '', 7)
            for reg in registros:
                if reg['tipo_dialisis'] == 'Manual':
                    pdf.cell(col_widths[0], 5, str(reg.get('id', '')), 1, 0, 'C')
                    
                    # Fecha completa
                    fecha_str = reg.get('fecha', '')[-5:] if reg.get('fecha') else ''
                    if reg.get('fecha'):
                        fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
                        fecha_str = fecha_obj.strftime('%d/%m/%Y')
                    pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
                    
                    pdf.cell(col_widths[2], 5, reg.get('hora', '')[:5] if reg.get('hora') else '', 1, 0, 'C')
                    pdf.cell(col_widths[3], 5, 'Manual', 1, 0, 'C')  # Tipo completo
                    pdf.cell(col_widths[4], 5, reg.get('color_bolsa', '')[:3] if reg.get('color_bolsa') else '-', 1, 0, 'C')
                    pdf.cell(col_widths[5], 5, f"{reg.get('volumen_infundido_ml', 0)}", 1, 0, 'R')
                    pdf.cell(col_widths[6], 5, f"{reg.get('volumen_drenado_ml', 0)}", 1, 0, 'R')
                    
                    balance = reg.get('uf_recambio_manual_ml', 0)
                    if balance < 0:
                        pdf.set_text_color(255, 0, 0)
                    pdf.cell(col_widths[7], 5, f"{balance}", 1, 0, 'R')
                    pdf.set_text_color(0, 0, 0)
                    
                    obs = reg.get('observaciones', '')[:15]
                    if len(reg.get('observaciones', '')) > 15:
                        obs += '...'
                    pdf.cell(col_widths[8], 5, obs, 1, 0, 'L')
                    pdf.ln()
            pdf.ln(5)
        
        if hay_cicladoras:
            if hay_manuales:
                pdf.add_page()  # Nueva página para cicladoras si ya mostramos manuales
            
            # Tabla para registros de cicladora
            pdf.set_font('Arial', 'B', 8)
            headers = ['ID', 'Fecha', 'Inicio', 'Fin', 'UF', 'Efic', 'Bolsa1', 'Bolsa2', 'Obs']
            col_widths = [10, 22, 15, 15, 18, 18, 25, 25, 28]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
            pdf.ln()
            
            pdf.set_font('Arial', '', 7)
            for reg in registros:
                if reg['tipo_dialisis'] == 'Cicladora':
                    pdf.cell(col_widths[0], 5, str(reg.get('id', '')), 1, 0, 'C')
                    
                    # Fecha completa
                    fecha_str = reg.get('fecha', '')[-5:] if reg.get('fecha') else ''
                    if reg.get('fecha'):
                        fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
                        fecha_str = fecha_obj.strftime('%d/%m/%Y')
                    pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
                    
                    pdf.cell(col_widths[2], 5, reg.get('hora_inicio', '')[:5] if reg.get('hora_inicio') else '', 1, 0, 'C')
                    pdf.cell(col_widths[3], 5, reg.get('hora_fin', '')[:5] if reg.get('hora_fin') else '', 1, 0, 'C')
                    pdf.cell(col_widths[4], 5, f"{reg.get('uf_total_cicladora_ml', 0)}", 1, 0, 'R')
                    pdf.cell(col_widths[5], 5, f"{reg.get('eficiencia_ml_por_hora', 0):.0f}", 1, 0, 'R')
                    
                    # Bolsas (con color y volumen)
                    bolsa1 = f"{reg.get('concentracion_bolsa1', '')[:3]}:{reg.get('volumen_bolsa1_ml', 0)}" if reg.get('concentracion_bolsa1') else '-'
                    bolsa2 = f"{reg.get('concentracion_bolsa2', '')[:3]}:{reg.get('volumen_bolsa2_ml', 0)}" if reg.get('concentracion_bolsa2') else '-'
                    pdf.cell(col_widths[6], 5, bolsa1, 1, 0, 'C')
                    pdf.cell(col_widths[7], 5, bolsa2, 1, 0, 'C')
                    
                    obs = reg.get('observaciones', '')[:15]
                    if len(reg.get('observaciones', '')) > 15:
                        obs += '...'
                    pdf.cell(col_widths[8], 5, obs, 1, 0, 'L')
                    pdf.ln()
    
    # Guardar PDF
    filename = f"informe_dialisis_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
    pdf.output(filename)
    return filename
