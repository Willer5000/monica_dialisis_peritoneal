import streamlit as st
# ============================================================
# VERIFICACIÓN DE CONEXIÓN (AGREGAR TEMPORALMENTE)
# ============================================================
import os
st.write("🔍 Verificando variables de entorno:")
st.write(f"SUPABASE_URL existe: {'SÍ' if os.getenv('SUPABASE_URL') else 'NO'}")
st.write(f"SUPABASE_KEY existe: {'SÍ' if os.getenv('SUPABASE_KEY') else 'NO'}")

try:
    from utils.database import Database
    db = Database()
    config = db.get_configuracion()
except Exception as e:
    st.error(f"❌ Error conectando a Supabase: {e}")
    st.stop()
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from utils.database import Database, BAIRES_TZ
from utils.pdf_generator import generar_informe_pdf
import os
import base64

# Configuración de la página
st.set_page_config(
    page_title="Diálisis Peritoneal - Mónica",
    page_icon="🍥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .paciente-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .boton-menu {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        margin: 0.5rem 0;
        border: none;
        width: 100%;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .boton-menu:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        background: #f0f0f0;
    }
    .ultimo-registro {
        background: #e6fffa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #48bb78;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        color: white;
        margin-top: 2rem;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar conexión a base de datos
@st.cache_resource
def init_db():
    return Database()

db = init_db()

# ============================================================
# BARRA LATERAL - ÚLTIMO REGISTRO
# ============================================================
with st.sidebar:
    st.markdown("### 📋 Último Registro")
    ultimo = db.get_ultimo_registro()
    
    if ultimo:
        fecha = datetime.strptime(ultimo['fecha'], '%Y-%m-%d')
        uf_valor = ultimo.get('uf_mostrar', 0)
        
        # Determinar color según UF
        if uf_valor > 0:
            color_uf = "#48bb78"  # Verde
            icono_uf = "✅"
            mensaje_uf = f"Eliminó {uf_valor:.0f} ml"
        elif uf_valor < 0:
            color_uf = "#f56565"  # Rojo
            icono_uf = "⚠️"
            mensaje_uf = f"Retuvo {abs(uf_valor):.0f} ml"
        else:
            color_uf = "#718096"  # Gris
            icono_uf = "⚖️"
            mensaje_uf = "Balance neutro"
        
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 10px; 
                    border-left: 4px solid {color_uf}; margin: 1rem 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 1.1rem; font-weight: bold;">
                📅 {fecha.strftime('%d/%m/%Y')} {ultimo['hora'][:5]}
            </div>
            <div style="margin-top: 0.5rem;">
                <span style="background: #e2e8f0; padding: 0.2rem 0.5rem; border-radius: 15px;">
                    {ultimo['tipo_dialisis']}
                </span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 1.2rem; font-weight: bold; color: {color_uf};">
                {icono_uf} {mensaje_uf}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #718096;">
                UF Total del día: {ultimo.get('uf_total_dia_ml', 0):.0f} ml
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar observaciones si existen
        if ultimo.get('observaciones'):
            st.markdown(f"📝 *{ultimo['observaciones']}*")
    else:
        st.info("No hay registros aún")
    
    st.markdown("---")
    st.markdown(f"🕒 **Hora BA:** {datetime.now(BAIRES_TZ).strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# ENCABEZADO PRINCIPAL
# ============================================================
config = db.get_configuracion()

st.markdown(f"""
<div class="main-header">
    <h1>🍥 Diálisis Peritoneal</h1>
    <h2>{config['nombre']}</h2>
</div>
""", unsafe_allow_html=True)

# Tarjeta del paciente
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Edad", f"{config['edad']} años")
with col2:
    st.metric("Peso", f"{config['peso_kg']} kg")
with col3:
    st.metric("Altura", f"{config['altura_m']} m")
with col4:
    st.metric("DNI", config['dni'])

st.markdown("---")

# ============================================================
# MENÚ PRINCIPAL
# ============================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕ NUEVO REGISTRO", use_container_width=True):
        st.session_state.pagina = "nuevo"
    if st.button("✏️ MODIFICAR", use_container_width=True):
        st.session_state.pagina = "modificar"

with col2:
    if st.button("🗑️ ELIMINAR", use_container_width=True):
        st.session_state.pagina = "eliminar"
    if st.button("📄 INFORME PDF", use_container_width=True):
        st.session_state.pagina = "informe"

with col3:
    if st.button("⚖️ ACTUALIZAR PESO", use_container_width=True):
        st.session_state.pagina = "peso"
    if st.button("📊 VER REGISTROS", use_container_width=True):
        st.session_state.pagina = "ver"

# ============================================================
# PÁGINAS
# ============================================================
if 'pagina' not in st.session_state:
    st.session_state.pagina = "principal"

# Página: Nuevo Registro
# Página: Ver Registros
if st.session_state.pagina == "ver":
    st.markdown("---")
    st.subheader("📊 Historial de Registros")
    
    # Obtener todos los registros
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    
    if registros:
        df = pd.DataFrame(registros)
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Calcular UF a mostrar según tipo
        df['uf_mostrar'] = df.apply(
            lambda x: x['uf_total_cicladora_ml'] if x['tipo_dialisis'] == 'Cicladora' 
            else x['uf_recambio_manual_ml'], axis=1
        )
        
        # Crear columna de UF por registro
        df['uf_mostrar'] = df.apply(
            lambda x: x['uf_total_cicladora_ml'] if x['tipo_dialisis'] == 'Cicladora' 
            else x['uf_recambio_manual_ml'], axis=1
        )
        
        # Agrupar por día para gráficos diarios
        df_diario = df.groupby(df['fecha'].dt.date).agg({
            'uf_mostrar': 'sum',  # Sumar todas las UF del día
            'tipo_dialisis': lambda x: 'Mixto' if (x == 'Cicladora').any() and (x == 'Manual').any() 
                                         else ('Cicladora' if (x == 'Cicladora').all() else 'Manual'),
            'id': 'count'
        }).reset_index()
        df_diario.columns = ['fecha', 'uf_total_dia', 'tipo_dia', 'num_registros']
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fecha_min = df['fecha'].min().date()
            fecha_max = df['fecha'].max().date()
            fecha_inicio = st.date_input("Fecha inicio", fecha_min, format="DD/MM/YYYY")
        with col2:
            fecha_fin = st.date_input("Fecha fin", fecha_max, format="DD/MM/YYYY")
        
        # Filtrar
        mask = (df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)
        df_filtrado = df[mask]
        df_diario_filtrado = df_diario[
            (df_diario['fecha'] >= fecha_inicio) & 
            (df_diario['fecha'] <= fecha_fin)
        ]
        
        # ============================================================
        # MÉTRICAS CLAVE DEL PERÍODO
        # ============================================================
        st.markdown("### 📈 Métricas Clave del Período")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Días con registro", len(df_diario_filtrado))
        with col2:
            uf_promedio = df_diario_filtrado['uf_total_dia'].mean()
            delta_uf = uf_promedio - df_diario_filtrado['uf_total_dia'].iloc[-1] if len(df_diario_filtrado) > 0 else 0
            st.metric("UF Promedio/día", f"{uf_promedio:.0f} ml", delta=f"{delta_uf:.0f}")
        with col3:
            uf_negativas = len(df_diario_filtrado[df_diario_filtrado['uf_total_dia'] < 0])
            st.metric("⚠️ Días con UF negativa", uf_negativas)
        with col4:
            total_registros = len(df_filtrado)
            st.metric("Total registros", total_registros)
        
        # ============================================================
        # GRÁFICO 1: EVOLUCIÓN DIARIA DE UF (TENDENCIA)
        # ============================================================
        st.markdown("### 📉 Evolución Diaria de Ultrafiltración")
        
        fig1 = go.Figure()
        
        # Línea de UF diaria
        fig1.add_trace(go.Scatter(
            x=df_diario_filtrado['fecha'],
            y=df_diario_filtrado['uf_total_dia'],
            mode='lines+markers',
            name='UF Total del día',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#667eea'),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>UF: %{y:.0f} ml<extra></extra>'
        ))
        
        # Línea de referencia en 0
        fig1.add_hline(y=0, line_dash="dash", line_color="red", 
                      annotation_text="Balance Neutro")
        
        # Línea de tendencia (media móvil de 3 días)
        if len(df_diario_filtrado) >= 3:
            df_diario_filtrado['tendencia'] = df_diario_filtrado['uf_total_dia'].rolling(3, min_periods=1).mean()
            fig1.add_trace(go.Scatter(
                x=df_diario_filtrado['fecha'],
                y=df_diario_filtrado['tendencia'],
                mode='lines',
                name='Tendencia (3 días)',
                line=dict(color='#48bb78', width=2, dash='dot')
            ))
        
        fig1.update_layout(
            title='Evolución de UF por Día',
            xaxis_title='Fecha',
            yaxis_title='Ultrafiltración (ml)',
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # ============================================================
        # GRÁFICO 2: COMPARATIVA CICLADORA VS MANUAL
        # ============================================================
        st.markdown("### 🔄 Comparativa Cicladora vs Manual")
        
        # Separar datos por tipo
        df_cicladora = df_filtrado[df_filtrado['tipo_dialisis'] == 'Cicladora']
        df_manual = df_filtrado[df_filtrado['tipo_dialisis'] == 'Manual']
        
        fig2 = go.Figure()
        
        if not df_cicladora.empty:
            fig2.add_trace(go.Scatter(
                x=df_cicladora['fecha'],
                y=df_cicladora['uf_total_cicladora_ml'],
                mode='markers',
                name='Cicladora',
                marker=dict(size=10, color='#4299e1', symbol='circle'),
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Cicladora UF: %{y:.0f} ml<extra></extra>'
            ))
        
        if not df_manual.empty:
            fig2.add_trace(go.Scatter(
                x=df_manual['fecha'],
                y=df_manual['uf_recambio_manual_ml'],
                mode='markers',
                name='Manual',
                marker=dict(size=10, color='#ed8936', symbol='square'),
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Manual UF: %{y:.0f} ml<extra></extra>'
            ))
        
        fig2.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig2.update_layout(
            title='UF por Tipo de Diálisis',
            xaxis_title='Fecha',
            yaxis_title='Ultrafiltración (ml)',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # ============================================================
        # GRÁFICO 3: DISTRIBUCIÓN DE UF
        # ============================================================
        st.markdown("### 📊 Distribución de UF")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma de UF
            fig3 = px.histogram(
                df_diario_filtrado, 
                x='uf_total_dia',
                nbins=20,
                title='Distribución de UF Diaria',
                labels={'uf_total_dia': 'UF (ml)', 'count': 'Frecuencia'},
                color_discrete_sequence=['#667eea']
            )
            fig3.add_vline(x=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Box plot por tipo de día
            fig4 = px.box(
                df_filtrado,
                x='tipo_dialisis',
                y='uf_mostrar',
                title='Distribución UF por Tipo',
                labels={'tipo_dialisis': 'Tipo', 'uf_mostrar': 'UF (ml)'},
                color='tipo_dialisis',
                color_discrete_map={'Cicladora': '#4299e1', 'Manual': '#ed8936'}
            )
            fig4.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig4, use_container_width=True)
        
        # ============================================================
        # TABLA DE DATOS
        # ============================================================
        st.markdown("### 📋 Detalle de Registros")
        
        # Preparar datos para tabla
        mostrar_cols = ['id', 'fecha', 'hora', 'tipo_dialisis', 
                       'uf_recambio_manual_ml', 'uf_total_cicladora_ml',
                       'color_bolsa', 'observaciones']
        
        df_mostrar = df_filtrado[mostrar_cols].copy()
        df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%d/%m/%Y')
        df_mostrar['hora'] = df_mostrar['hora'].str[:5]
        
        # Crear columna de UF según tipo
        df_mostrar['UF (ml)'] = df_mostrar.apply(
            lambda x: x['uf_total_cicladora_ml'] if x['tipo_dialisis'] == 'Cicladora' 
            else x['uf_recambio_manual_ml'], axis=1
        )
        
        # Seleccionar y renombrar columnas finales
        df_final = df_mostrar[['id', 'fecha', 'hora', 'tipo_dialisis', 'UF (ml)', 
                               'color_bolsa', 'observaciones']]
        df_final.columns = ['ID', 'Fecha', 'Hora', 'Tipo', 'UF (ml)', 
                           'Color', 'Observaciones']
        
        # Aplicar color a UF negativas
        def highlight_uf(val):
            if pd.notna(val) and val < 0:
                return 'color: red; font-weight: bold'
            return ''
        
        st.dataframe(
            df_final.style.applymap(highlight_uf, subset=['UF (ml)']),
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Exportar a CSV
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"registros_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("No hay registros aún. Comienza agregando un nuevo registro desde el menú principal.")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()

# Página: Nuevo Registro
# Página: Nuevo Registro (reemplaza esta sección completa)
if st.session_state.pagina == "nuevo":
    st.markdown("---")
    st.subheader("➕ Nuevo Registro de Diálisis")
    
    tipo = st.radio("Seleccionar tipo:", ["Manual", "Cicladora"], horizontal=True)
    
    if tipo == "Manual":
        with st.form("form_manual"):
            st.markdown("### 🖐️ Diálisis Manual")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.now(BAIRES_TZ), format="DD/MM/YYYY")
            with col2:
                hora = st.time_input("Hora", datetime.now(BAIRES_TZ).time())
            
            concentracion = st.selectbox("Concentración (Color)", ["Amarillo", "Verde", "Rojo"])
            
            st.markdown("#### ⚖️ Pesos (en kg)")
            col1, col2, col3 = st.columns(3)
            with col1:
                peso_llena = st.number_input("Peso bolsa llena (infusión)", min_value=0.0, step=0.1, format="%.1f", value=2.0)
                st.caption("Bolsa de solución NUEVA")
            with col2:
                peso_vacia = st.number_input("Peso bolsa vacía (opcional)", min_value=0.0, step=0.1, format="%.1f", value=0.0)
                st.caption("Bolsa después de infundir")
            with col3:
                peso_drenaje = st.number_input("Peso bolsa drenaje", min_value=0.0, step=0.1, format="%.1f", value=2.2)
                st.caption("Bolsa con líquido drenado")
            
            # Mostrar volúmenes calculados
            if peso_llena > 0:
                vol_infundido = (peso_llena - peso_vacia) * 1000
                vol_drenado = peso_drenaje * 1000
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Volumen infundido", f"{vol_infundido:.0f} ml")
                with col2:
                    st.metric("Volumen drenado", f"{vol_drenado:.0f} ml")
            
            observaciones = st.text_area("📝 Observaciones")
            
            if st.form_submit_button("💾 Guardar Registro Manual", use_container_width=True):
                datos = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'hora': hora.strftime("%H:%M:%S"),
                    'concentracion': concentracion,
                    'peso_llena': peso_llena,
                    'peso_vacia': peso_vacia,
                    'peso_drenaje': peso_drenaje,
                    'observaciones': observaciones
                }
                try:
                    db.insert_registro_manual(datos)
                    st.success("✅ Registro manual guardado")
                    st.balloons()
                    st.session_state.pagina = "principal"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    else:  # Cicladora (igual que antes)
        with st.form("form_cicladora"):
            st.markdown("### 🤖 Diálisis con Cicladora")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.now(BAIRES_TZ), format="DD/MM/YYYY")
                hora_inicio = st.time_input("Hora inicio", datetime.now(BAIRES_TZ).time())
            with col2:
                hora_fin = st.time_input("Hora fin", (datetime.now(BAIRES_TZ) + timedelta(hours=8)).time())
            
            st.markdown("#### 📊 Datos de la máquina")
            col1, col2 = st.columns(2)
            with col1:
                drenaje_inicial = st.number_input("Vol. drenaje inicial (ml)", min_value=0, step=50)
                uf_total = st.number_input("UF Total (ml)", min_value=0, step=50)
                tiempo_permanencia = st.number_input("Tiempo permanencia promedio (min)", min_value=0, step=5)
            with col2:
                tiempo_perdido = st.number_input("Tiempo perdido (min)", min_value=0, step=5)
                volumen_solucion = st.number_input("Vol. total solución (ml)", min_value=0, step=100)
                num_ciclos = st.number_input("Número de ciclos", min_value=1, step=1, value=4)
            
            observaciones = st.text_area("📝 Observaciones")
            
            if st.form_submit_button("💾 Guardar Registro Cicladora", use_container_width=True):
                datos = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'hora_inicio': hora_inicio.strftime("%H:%M:%S"),
                    'hora_fin': hora_fin.strftime("%H:%M:%S"),
                    'drenaje_inicial': drenaje_inicial,
                    'uf_total': uf_total,
                    'tiempo_permanencia': tiempo_permanencia,
                    'tiempo_perdido': tiempo_perdido,
                    'volumen_solucion': volumen_solucion,
                    'num_ciclos': num_ciclos,
                    'observaciones': observaciones
                }
                try:
                    db.insert_registro_cicladora(datos)
                    st.success("✅ Registro de cicladora guardado")
                    st.balloons()
                    st.session_state.pagina = "principal"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()
        
# Página: Informe PDF
if st.session_state.pagina == "informe":
    st.markdown("---")
    st.subheader("📄 Generar Informe PDF")
    
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    
    if registros:
        fechas = [datetime.strptime(r['fecha'], '%Y-%m-%d') for r in registros]
        fecha_min = min(fechas).date()
        fecha_max = max(fechas).date()
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("📅 Fecha inicio", fecha_min, format="DD/MM/YYYY")
        with col2:
            fecha_fin = st.date_input("📅 Fecha fin", fecha_max, format="DD/MM/YYYY")
        
        tipo_informe = st.radio(
            "📋 Tipo de informe",
            ["completo", "base", "resumen"],
            format_func=lambda x: {
                "completo": "📑 Completo (Base + Resumen)",
                "base": "📊 Solo Base de Datos",
                "resumen": "📈 Solo Resumen"
            }[x],
            horizontal=True
        )
        
        if st.button("📥 Generar PDF", use_container_width=True):
            with st.spinner("Generando informe..."):
                registros_filtrados = db.get_registros_fecha(
                    fecha_inicio.strftime("%Y-%m-%d"),
                    fecha_fin.strftime("%Y-%m-%d")
                )
                estadisticas = db.get_estadisticas_periodo(
                    fecha_inicio.strftime("%Y-%m-%d"),
                    fecha_fin.strftime("%Y-%m-%d")
                )
                
                filename = generar_informe_pdf(
                    registros_filtrados,
                    estadisticas,
                    fecha_inicio.strftime("%d/%m/%Y"),
                    fecha_fin.strftime("%d/%m/%Y"),
                    tipo_informe
                )
                
                with open(filename, "rb") as f:
                    pdf_data = f.read()
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{filename}">📥 Descargar PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("✅ PDF generado")
                os.remove(filename)
    else:
        st.info("No hay datos para generar informe")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()

if st.session_state.pagina == "peso":
    st.markdown("---")
    st.subheader("⚖️ Actualizar Peso y Altura")
    
    with st.form("form_peso"):
        nuevo_peso = st.number_input("Nuevo Peso (kg)", 
                                     min_value=30.0, max_value=200.0, 
                                     value=float(config['peso_kg']), 
                                     step=0.1, format="%.1f")
        nueva_altura = st.number_input("Nueva Altura (m)", 
                                       min_value=1.0, max_value=2.5, 
                                       value=float(config['altura_m']), 
                                       step=0.01, format="%.2f")
        
        if st.form_submit_button("💾 Actualizar", use_container_width=True):
            try:
                db.update_configuracion(nuevo_peso, nueva_altura)
                st.success("✅ Peso y altura actualizados")
                st.balloons()
                st.session_state.pagina = "principal"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()



# Página: Modificar
if st.session_state.pagina == "modificar":
    st.markdown("---")
    st.subheader("✏️ Modificar Registro")
    st.warning("Funcionalidad en desarrollo - Por ahora elimina y crea uno nuevo")
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()

# Página: Eliminar
if st.session_state.pagina == "eliminar":
    st.markdown("---")
    st.subheader("🗑️ Eliminar Registro")
    
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    if registros:
        # Mostrar selector de ID
        opciones = {f"{r['id']} - {r['fecha']} - {r['tipo_dialisis']}": r['id'] for r in registros[:10]}
        seleccion = st.selectbox("Selecciona registro a eliminar:", list(opciones.keys()))
        
        if st.button("🗑️ Confirmar eliminación", type="primary"):
            st.info("Eliminación deshabilitada temporalmente")
    else:
        st.info("No hay registros para eliminar")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()


# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    Aplicación para Mónica Rojas · Datos guardados en Supabase (PostgreSQL)<br>
    ⚕️ Registro de Diálisis Peritoneal - Versión 1.0
</div>
""", unsafe_allow_html=True)
