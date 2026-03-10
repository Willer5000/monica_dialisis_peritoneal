from fpdf import FPDF
from datetime import datetime
import os
import matplotlib.pyplot as plt
import io
import tempfile

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

def generar_grafico_evolucion(fechas, valores, titulo, color='#667eea'):
    """Genera un gráfico de evolución y lo guarda como imagen temporal"""
    plt.figure(figsize=(10, 5))
    
    # Convertir fechas a formato legible
    fechas_str = [fecha[-5:] if len(fecha) > 5 else fecha for fecha in fechas]
    
    plt.plot(fechas_str, valores, marker='o', linestyle='-', linewidth=2, color=color, markersize=6)
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Balance Neutro')
    plt.title(titulo, fontsize=14, pad=20)
    plt.xlabel('Fecha', fontsize=11)
    plt.ylabel('Ultrafiltración (ml)', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=100, bbox_inches='tight')
    plt.close()
    
    return temp_file.name

def generar_grafico_barras_comparativo(fechas, valores_cici, valores_manual, titulo):
    """Genera gráfico de barras comparativo entre cicladora y manual"""
    plt.figure(figsize=(10, 5))
    
    fechas_str = [fecha[-5:] for fecha in fechas]
    x = range(len(fechas_str))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 5))
    rects1 = ax.bar([i - width/2 for i in x], valores_cici, width, label='Cicladora', color='#4299e1')
    rects2 = ax.bar([i + width/2 for i in x], valores_manual, width, label='Manual', color='#ed8936')
    
    ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax.set_xlabel('Fecha', fontsize=11)
    ax.set_ylabel('Ultrafiltración (ml)', fontsize=11)
    ax.set_title(titulo, fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(fechas_str, rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=100, bbox_inches='tight')
    plt.close()
    
    return temp_file.name

def generar_grafico_torta_distribucion(manuales, cicladoras, total_uf):
    """Genera gráfico de torta con distribución de UF por tipo"""
    plt.figure(figsize=(8, 6))
    
    labels = ['Manual', 'Cicladora']
    sizes = [manuales, cicladoras]
    colors = ['#ed8936', '#4299e1']
    explode = (0.05, 0)
    
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.axis('equal')
    plt.title(f'Distribución de UF Total: {total_uf:.0f} ml', fontsize=14)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=100, bbox_inches='tight')
    plt.close()
    
    return temp_file.name

def generar_informe_pdf(registros, estadisticas, fecha_inicio, fecha_fin, tipo_informe):
    """Genera PDF con informe completo del periodo seleccionado y gráficos"""
    
    pdf = PDFReport()
    
    if tipo_informe == 'base':
        pdf = PDFReport(orientation='L')  # Horizontal para base de datos
    else:
        pdf = PDFReport()  # Vertical para informes con gráficos
    
    pdf.add_page()
    
    # ============================================================
    # ENCABEZADO DEL INFORME
    # ============================================================
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Periodo: {fecha_inicio} al {fecha_fin}', 0, 1)
    pdf.cell(0, 8, f'Fecha de generacion: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(5)
    
    # ============================================================
    # INFORME RESUMEN
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
            
            # Encabezados
            pdf.set_font('Arial', 'B', 9)
            col_widths = [35, 30, 30, 30, 35]
            headers = ['Fecha', 'UF Cici', 'Manuales', 'UF Manual', 'UF Total']
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 7, header, 1, 0, 'C')
            pdf.ln()
            
            # Datos
            pdf.set_font('Arial', '', 8)
            for fecha, datos_dia in estadisticas['dias'].items():
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
                fecha_str = fecha_obj.strftime('%d/%m/%Y')
                
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
    # GRÁFICOS EN HOJAS SEPARADAS (ANEXOS)
    # ============================================================
    if tipo_informe in ['resumen', 'completo'] and estadisticas:
        # Gráfico 1 - Evolución
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'ANEXO 1 - Evolución de UF Diaria', 0, 1, 'C')
        pdf.ln(5)
        
        if estadisticas.get('fechas') and estadisticas.get('uf_por_dia'):
            archivo_grafico = generar_grafico_evolucion(
                estadisticas['fechas'],
                estadisticas['uf_por_dia'],
                'Evolución de Ultrafiltración Diaria'
            )
            if os.path.exists(archivo_grafico):
                pdf.image(archivo_grafico, x=10, y=pdf.get_y(), w=190)
                os.unlink(archivo_grafico)
        
        # Gráfico 2 - Comparativa (solo si hay datos)
        uf_cicladora_por_dia = []
        uf_manual_por_dia = []
        fechas_lista = []
        
        for fecha, datos in estadisticas['dias'].items():
            fechas_lista.append(fecha)
            uf_cicladora_por_dia.append(datos.get('uf_cicladora', 0))
            uf_manual_por_dia.append(datos.get('uf_manual', 0))
        
        if any(uf_cicladora_por_dia) and any(uf_manual_por_dia):
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'ANEXO 2 - Comparativa Cicladora vs Manual', 0, 1, 'C')
            pdf.ln(5)
            
            archivo_comparativo = generar_grafico_barras_comparativo(
                fechas_lista,
                uf_cicladora_por_dia,
                uf_manual_por_dia,
                'Comparativa UF por Tipo'
            )
            if os.path.exists(archivo_comparativo):
                pdf.image(archivo_comparativo, x=10, y=pdf.get_y(), w=190)
                os.unlink(archivo_comparativo)
        
        # Gráfico 3 - Distribución
        if estadisticas.get('uf_cicladora_total', 0) > 0 or estadisticas.get('uf_manual_total', 0) > 0:
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'ANEXO 3 - Distribución de UF', 0, 1, 'C')
            pdf.ln(5)
            
            archivo_torta = generar_grafico_torta_distribucion(
                estadisticas.get('uf_manual_total', 0),
                estadisticas.get('uf_cicladora_total', 0),
                estadisticas.get('uf_total_periodo', 0)
            )
            if os.path.exists(archivo_torta):
                pdf.image(archivo_torta, x=50, y=pdf.get_y(), w=110)
                os.unlink(archivo_torta)
    
    # ============================================================
    # BASE DE DATOS (registros detallados)
    # ============================================================
    if tipo_informe in ['base', 'completo'] and registros:
        if tipo_informe == 'completo':
            pdf.add_page()
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'DETALLE DE REGISTROS', 0, 1)
        pdf.ln(5)
        
        # Separar por tipo
        manuales = [r for r in registros if r['tipo_dialisis'] == 'Manual']
        cicladoras = [r for r in registros if r['tipo_dialisis'] == 'Cicladora']
        
        if manuales:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Registros Manuales:', 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 8)
            headers = ['ID', 'Fecha', 'Hora', 'Color', 'Infundido', 'Drenado', 'Balance', 'Obs']
            col_widths = [10, 22, 15, 18, 25, 25, 25, 28]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
            pdf.ln()
            
            pdf.set_font('Arial', '', 7)
            for reg in manuales:
                pdf.cell(col_widths[0], 5, str(reg.get('id', '')), 1, 0, 'C')
                
                if reg.get('fecha'):
                    fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                else:
                    fecha_str = ''
                pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
                
                pdf.cell(col_widths[2], 5, reg.get('hora', '')[:5] if reg.get('hora') else '', 1, 0, 'C')
                pdf.cell(col_widths[3], 5, reg.get('color_bolsa', '')[:3] if reg.get('color_bolsa') else '-', 1, 0, 'C')
                pdf.cell(col_widths[4], 5, f"{reg.get('volumen_infundido_ml', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[5], 5, f"{reg.get('volumen_drenado_ml', 0)}", 1, 0, 'R')
                
                balance = reg.get('uf_recambio_manual_ml', 0)
                if balance < 0:
                    pdf.set_text_color(255, 0, 0)
                pdf.cell(col_widths[6], 5, f"{balance}", 1, 0, 'R')
                pdf.set_text_color(0, 0, 0)
                
                obs = reg.get('observaciones', '')[:15]
                if len(reg.get('observaciones', '')) > 15:
                    obs += '...'
                pdf.cell(col_widths[7], 5, obs, 1, 0, 'L')
                pdf.ln()
            pdf.ln(5)
        
        if cicladoras:
            if manuales:
                pdf.add_page()
            
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'REGISTROS DE CICLADORA - DATOS DE LA MÁQUINA', 0, 1)
            pdf.ln(5)
            
            # Tabla principal con datos de la máquina
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, 'Valores mostrados por la cicladora:', 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 8)
            headers = ['ID', 'Fecha', 'UF Total', 'Dren.Ini', 'T.Perm', 'T.Perd', 'Ciclos', 'Efic']
            col_widths = [10, 22, 20, 20, 20, 18, 15, 20]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
            pdf.ln()
            
            pdf.set_font('Arial', '', 7)
            for reg in cicladoras:
                pdf.cell(col_widths[0], 5, str(reg.get('id', '')), 1, 0, 'C')
                
                if reg.get('fecha'):
                    fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                else:
                    fecha_str = ''
                pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
                
                pdf.cell(col_widths[2], 5, f"{reg.get('uf_total_cicladora_ml', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[3], 5, f"{reg.get('vol_drenaje_inicial_ml', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[4], 5, f"{reg.get('tiempo_permanencia_promedio_min', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[5], 5, f"{reg.get('tiempo_perdido_min', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[6], 5, f"{reg.get('numero_ciclos_completados', 0)}", 1, 0, 'R')
                pdf.cell(col_widths[7], 5, f"{reg.get('eficiencia_ml_por_hora', 0):.0f}", 1, 0, 'R')
                pdf.ln()
            
            pdf.ln(5)
            
            # Tabla de bolsas utilizadas
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, 'Bolsas utilizadas:', 0, 1)
            pdf.ln(2)
            
            pdf.set_font('Arial', 'B', 8)
            headers_bolsas = ['ID', 'Fecha', 'Bolsa 1', 'Bolsa 2', 'Observaciones']
            col_widths_bolsas = [10, 22, 25, 25, 50]
            
            for i, header in enumerate(headers_bolsas):
                pdf.cell(col_widths_bolsas[i], 6, header, 1, 0, 'C')
            pdf.ln()
            
            pdf.set_font('Arial', '', 7)
            for reg in cicladoras:
                pdf.cell(col_widths_bolsas[0], 5, str(reg.get('id', '')), 1, 0, 'C')
                
                if reg.get('fecha'):
                    fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                else:
                    fecha_str = ''
                pdf.cell(col_widths_bolsas[1], 5, fecha_str, 1, 0, 'C')
                
                bolsa1 = reg.get('concentracion_bolsa1', '') if reg.get('concentracion_bolsa1') else '-'
                pdf.cell(col_widths_bolsas[2], 5, bolsa1, 1, 0, 'C')
                
                bolsa2 = reg.get('concentracion_bolsa2', '') if reg.get('concentracion_bolsa2') else '-'
                pdf.cell(col_widths_bolsas[3], 5, bolsa2, 1, 0, 'C')
                
                obs = reg.get('observaciones', '')[:40]
                if len(reg.get('observaciones', '')) > 40:
                    obs += '...'
                pdf.cell(col_widths_bolsas[4], 5, obs, 1, 0, 'L')
                pdf.ln()
    
    # Guardar PDF
    filename = f"informe_dialisis_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
    pdf.output(filename)
    return filename
