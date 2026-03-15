from fpdf import FPDF
from datetime import datetime
import os
import matplotlib.pyplot as plt
import tempfile
import zipfile
from io import BytesIO

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
    plt.figure(figsize=(10, 5))
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

def generar_pdf_resumen(estadisticas, fecha_inicio, fecha_fin):
    """Genera PDF con resumen estadístico y gráficos (vertical)"""
    pdf = PDFReport()
    pdf.add_page()

    # Encabezado
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Periodo: {fecha_inicio} al {fecha_fin}', 0, 1)
    pdf.cell(0, 8, f'Fecha de generacion: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
    pdf.ln(5)

    if not estadisticas:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, 'No hay datos para el período seleccionado.', 0, 1)
        filename = f"resumen_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
        pdf.output(filename)
        return filename

    # Título
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RESUMEN ESTADISTICO DEL PERIODO', 0, 1)
    pdf.ln(2)

    # Gráfico 1: Evolución
    if estadisticas.get('fechas') and estadisticas.get('uf_por_dia'):
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, 'Evolución de UF por Día:', 0, 1)
        pdf.ln(2)
        archivo = generar_grafico_evolucion(estadisticas['fechas'], estadisticas['uf_por_dia'], '')
        pdf.image(archivo, x=10, y=pdf.get_y(), w=190)
        pdf.ln(70)
        os.unlink(archivo)

    # Gráfico 2: Comparativa (si hay ambos)
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
        pdf.cell(0, 10, 'COMPARATIVA CICLADORA VS MANUAL', 0, 1, 'C')
        pdf.ln(5)
        archivo = generar_grafico_barras_comparativo(fechas_lista, uf_cicladora_por_dia, uf_manual_por_dia, '')
        pdf.image(archivo, x=10, y=pdf.get_y(), w=190)
        pdf.ln(70)
        os.unlink(archivo)

    # Gráfico 3: Distribución
    if estadisticas.get('uf_cicladora_total', 0) > 0 or estadisticas.get('uf_manual_total', 0) > 0:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'DISTRIBUCIÓN DE UF', 0, 1, 'C')
        pdf.ln(5)
        archivo = generar_grafico_torta_distribucion(
            estadisticas.get('uf_manual_total', 0),
            estadisticas.get('uf_cicladora_total', 0),
            estadisticas.get('uf_total_periodo', 0)
        )
        pdf.image(archivo, x=45, y=pdf.get_y(), w=120)
        pdf.ln(70)
        os.unlink(archivo)

    # Tabla de resumen diario
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'RESUMEN DIARIO', 0, 1, 'C')
    pdf.ln(5)

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
    pdf.ln(5)

    # Guardar
    filename = f"resumen_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
    pdf.output(filename)
    return filename

def generar_pdf_base(registros, fecha_inicio, fecha_fin):
    """Genera PDF con la base de datos (horizontal) y sin columna ID"""
    pdf = PDFReport(orientation='L')
    pdf.add_page()

    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'REGISTROS DE DIÁLISIS', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Periodo: {fecha_inicio} al {fecha_fin}', 0, 1)
    pdf.ln(5)

    if not registros:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, 'No hay registros en el período.', 0, 1)
        filename = f"base_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
        pdf.output(filename)
        return filename

    # Separar por tipo para mejor visualización
    manuales = [r for r in registros if r['tipo_dialisis'] == 'Manual']
    cicladoras = [r for r in registros if r['tipo_dialisis'] == 'Cicladora']

    # --- TABLA MANUALES ---
    if manuales:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Registros Manuales:', 0, 1)
        pdf.ln(2)

        # Encabezados: N° (correlativo), Fecha, Hora, Color, Infundido, Drenado, Balance, Obs
        # Ocultamos ID, mostramos número de fila dentro del período
        pdf.set_font('Arial', 'B', 8)
        headers = ['N°', 'Fecha', 'Hora', 'Color', 'Infundido', 'Drenado', 'Balance', 'Observaciones']
        col_widths = [10, 22, 15, 15, 25, 25, 25, 45]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
        pdf.ln()

        pdf.set_font('Arial', '', 7)
        for idx, reg in enumerate(manuales, start=1):
            pdf.cell(col_widths[0], 5, str(idx), 1, 0, 'C')
            # Fecha
            fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
            fecha_str = fecha_obj.strftime('%d/%m/%Y')
            pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
            # Hora
            pdf.cell(col_widths[2], 5, reg.get('hora', '')[:5] if reg.get('hora') else '', 1, 0, 'C')
            # Color
            pdf.cell(col_widths[3], 5, reg.get('color_bolsa', '')[:3] if reg.get('color_bolsa') else '-', 1, 0, 'C')
            # Infundido
            pdf.cell(col_widths[4], 5, f"{reg.get('volumen_infundido_ml', 0)}", 1, 0, 'R')
            # Drenado
            pdf.cell(col_widths[5], 5, f"{reg.get('volumen_drenado_ml', 0)}", 1, 0, 'R')
            # Balance
            balance = reg.get('uf_recambio_manual_ml', 0)
            if balance < 0:
                pdf.set_text_color(255, 0, 0)
            pdf.cell(col_widths[6], 5, f"{balance}", 1, 0, 'R')
            pdf.set_text_color(0, 0, 0)
            # Observaciones
            obs = reg.get('observaciones', '')[:30]
            if len(reg.get('observaciones', '')) > 30:
                obs += '...'
            pdf.cell(col_widths[7], 5, obs, 1, 0, 'L')
            pdf.ln()
        pdf.ln(5)

    # --- TABLA CICLADORAS ---
    if cicladoras:
        if manuales:
            pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Registros de Cicladora:', 0, 1)
        pdf.ln(2)

        # Encabezados: N°, Fecha, Inicio, Fin, UF, Efic, Bolsa1, Bolsa2, Dren.Ini, Obs
        pdf.set_font('Arial', 'B', 7)
        headers = ['N°', 'Fecha', 'Inicio', 'Fin', 'UF', 'Efic', 'Bolsa1', 'Bolsa2', 'Dren.Ini', 'Obs']
        col_widths = [8, 18, 13, 13, 15, 15, 15, 15, 18, 40]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
        pdf.ln()

        pdf.set_font('Arial', '', 6.5)
        for idx, reg in enumerate(cicladoras, start=1):
            pdf.cell(col_widths[0], 5, str(idx), 1, 0, 'C')
            # Fecha
            fecha_obj = datetime.strptime(reg['fecha'], '%Y-%m-%d')
            fecha_str = fecha_obj.strftime('%d/%m/%Y')
            pdf.cell(col_widths[1], 5, fecha_str, 1, 0, 'C')
            # Inicio
            pdf.cell(col_widths[2], 5, reg.get('hora_inicio', '')[:5] if reg.get('hora_inicio') else '', 1, 0, 'C')
            # Fin
            pdf.cell(col_widths[3], 5, reg.get('hora_fin', '')[:5] if reg.get('hora_fin') else '', 1, 0, 'C')
            # UF
            pdf.cell(col_widths[4], 5, f"{reg.get('uf_total_cicladora_ml', 0)}", 1, 0, 'R')
            # Eficiencia
            pdf.cell(col_widths[5], 5, f"{reg.get('eficiencia_ml_por_hora', 0):.0f}", 1, 0, 'R')
            # Bolsa1
            bolsa1 = reg.get('concentracion_bolsa1', '')[:3] if reg.get('concentracion_bolsa1') else '-'
            pdf.cell(col_widths[6], 5, bolsa1, 1, 0, 'C')
            # Bolsa2
            bolsa2 = reg.get('concentracion_bolsa2', '')[:3] if reg.get('concentracion_bolsa2') else '-'
            pdf.cell(col_widths[7], 5, bolsa2, 1, 0, 'C')
            # Drenaje inicial
            pdf.cell(col_widths[8], 5, f"{reg.get('vol_drenaje_inicial_ml', 0)}", 1, 0, 'R')
            # Obs
            obs = reg.get('observaciones', '')[:20]
            if len(reg.get('observaciones', '')) > 20:
                obs += '...'
            pdf.cell(col_widths[9], 5, obs, 1, 0, 'L')
            pdf.ln()

    filename = f"base_{fecha_inicio.replace('/', '_')}_a_{fecha_fin.replace('/', '_')}.pdf"
    pdf.output(filename)
    return filename

def generar_informe_pdf(registros, estadisticas, fecha_inicio, fecha_fin, tipo_informe):
    """
    Genera PDF(s) según el tipo:
    - 'resumen': solo resumen (vertical)
    - 'base': solo base de datos (horizontal)
    - 'completo': genera ambos y devuelve una lista de nombres de archivo
    """
    if tipo_informe == 'resumen':
        return [generar_pdf_resumen(estadisticas, fecha_inicio, fecha_fin)]
    elif tipo_informe == 'base':
        return [generar_pdf_base(registros, fecha_inicio, fecha_fin)]
    else:  # completo
        archivos = []
        archivos.append(generar_pdf_resumen(estadisticas, fecha_inicio, fecha_fin))
        archivos.append(generar_pdf_base(registros, fecha_inicio, fecha_fin))
        return archivos
