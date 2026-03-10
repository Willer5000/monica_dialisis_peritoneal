import streamlit as st
import pandas as pd
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
        st.markdown(f"""
        <div class="ultimo-registro">
            <strong>📅 {fecha.strftime('%d/%m/%Y')} {ultimo['hora'][:5]}</strong><br>
            Tipo: {ultimo['tipo_dialisis']}<br>
            UF: {ultimo.get('uf_total_dia_ml', 0):.0f} ml<br>
            {'⚠️ UF Negativa' if ultimo.get('uf_total_dia_ml', 0) < 0 else '✓ Normal'}
        </div>
        """, unsafe_allow_html=True)
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
if st.session_state.pagina == "nuevo":
    st.markdown("---")
    st.subheader("➕ Nuevo Registro de Diálisis")
    
    with st.form("form_nuevo_registro"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", datetime.now(BAIRES_TZ), 
                                 format="DD/MM/YYYY")
        with col2:
            hora = st.time_input("Hora", datetime.now(BAIRES_TZ).time())
        
        tipo = st.selectbox("Tipo de Diálisis", ["Manual", "Cicladora"])
        
        if tipo == "Manual":
            st.markdown("##### 🖐️ Datos Manuales")
            col1, col2 = st.columns(2)
            with col1:
                color = st.selectbox("Color de Bolsa", ["Amarillo", "Verde", "Rojo"])
            with col2:
                pass
            
            col1, col2 = st.columns(2)
            with col1:
                peso_sol = st.number_input("⚖️ Peso Solución (kg)", 
                                          min_value=0.0, step=0.1, format="%.1f",
                                          help="Peso de la bolsa NUEVA")
            with col2:
                peso_dren = st.number_input("💧 Peso Drenaje (kg)", 
                                           min_value=0.0, step=0.1, format="%.1f",
                                           help="Peso de la bolsa de DRENAJE")
            
            if peso_sol > 0 and peso_dren > 0:
                uf_calc = (peso_dren - peso_sol) * 1000
                if uf_calc > 0:
                    st.success(f"✅ UF calculada: {uf_calc:.0f} ml (eliminó líquido)")
                elif uf_calc < 0:
                    st.error(f"⚠️ UF calculada: {uf_calc:.0f} ml (retuvo líquido)")
                else:
                    st.info(f"UF calculada: 0 ml (balance neutro)")
        else:
            st.markdown("##### 🤖 Datos Cicladora")
            uf_cic = st.number_input("UF Total (ml)", min_value=0, step=50,
                                    help="Ultrafiltración total de la máquina")
            st.info("La UF de cicladora se registra como valor total de la noche")
        
        observaciones = st.text_area("📝 Observaciones", placeholder="Ej: dolor, solución turbia, etc.")
        
        submitted = st.form_submit_button("💾 Guardar Registro", use_container_width=True)
        if submitted:
            datos = {
                'fecha': fecha.strftime("%Y-%m-%d"),
                'hora': hora.strftime("%H:%M:%S"),
                'tipo': tipo,
                'observaciones': observaciones
            }
            
            if tipo == "Manual":
                datos.update({
                    'color_bolsa': color,
                    'peso_solucion': peso_sol,
                    'peso_drenaje': peso_dren
                })
            else:
                datos['uf_cicladora'] = uf_cic
            
            try:
                resultado = db.insert_registro(datos)
                st.success("✅ Registro guardado correctamente")
                st.balloons()
                st.session_state.pagina = "principal"
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()

# Página: Actualizar Peso
elif st.session_state.pagina == "peso":
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
        
        submitted = st.form_submit_button("💾 Actualizar", use_container_width=True)
        if submitted:
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

# Página: Ver Registros
elif st.session_state.pagina == "ver":
    st.markdown("---")
    st.subheader("📊 Historial de Registros")
    
    # Obtener todos los registros
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    
    if registros:
        df = pd.DataFrame(registros)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['uf_mostrar'] = df.apply(
            lambda x: x['uf_total_cicladora_ml'] if x['tipo_dialisis'] == 'Cicladora' 
            else x['uf_recambio_manual_ml'], axis=1
        )
        
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
        
        # Métricas del período
        st.markdown("### 📈 Resumen del período")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total registros", len(df_filtrado))
        with col2:
            st.metric("UF promedio", f"{df_filtrado['uf_mostrar'].mean():.0f} ml")
        with col3:
            uf_negativas = len(df_filtrado[df_filtrado['uf_mostrar'] < 0])
            st.metric("⚠️ UF negativas", uf_negativas)
        with col4:
            st.metric("Manuales", len(df_filtrado[df_filtrado['tipo_dialisis'] == 'Manual']))
        
        # Gráfico de evolución
        st.markdown("### 📉 Evolución de UF")
        fig = px.line(df_filtrado.sort_values('fecha'), 
                     x='fecha', y='uf_mostrar',
                     title='Ultrafiltración por Registro',
                     labels={'fecha': 'Fecha', 'uf_mostrar': 'UF (ml)'})
        fig.add_hline(y=0, line_dash="dash", line_color="red", 
                     annotation_text="Balance Neutro")
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de datos
        st.markdown("### 📋 Detalle de registros")
        mostrar_cols = ['id', 'fecha', 'hora', 'tipo_dialisis', 'uf_mostrar', 
                       'color_bolsa', 'observaciones']
        df_mostrar = df_filtrado[mostrar_cols].copy()
        df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%d/%m/%Y')
        df_mostrar['hora'] = df_mostrar['hora'].str[:5]
        df_mostrar.columns = ['ID', 'Fecha', 'Hora', 'Tipo', 'UF (ml)', 
                              'Color', 'Observaciones']
        
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros aún")
    
    if st.button("← Volver al menú"):
        st.session_state.pagina = "principal"
        st.rerun()

# Página: Informe PDF
elif st.session_state.pagina == "informe":
    st.markdown("---")
    st.subheader("📄 Generar Informe PDF")
    
    # Obtener rango de fechas disponible
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    
    if registros:
        fechas = [datetime.strptime(r['fecha'], '%Y-%m-%d') for r in registros]
        fecha_min = min(fechas).date()
        fecha_max = max(fechas).date()
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("📅 Fecha inicio", 
                                        fecha_min,
                                        min_value=fecha_min,
                                        max_value=fecha_max,
                                        format="DD/MM/YYYY")
        with col2:
            fecha_fin = st.date_input("📅 Fecha fin", 
                                     fecha_max,
                                     min_value=fecha_min,
                                     max_value=fecha_max,
                                     format="DD/MM/YYYY")
        
        tipo_informe = st.radio(
            "📋 Tipo de informe",
            ["completo", "base", "resumen"],
            format_func=lambda x: {
                "completo": "📑 Completo (Base de datos + Resumen)",
                "base": "📊 Solo Base de Datos (Horizontal)",
                "resumen": "📈 Solo Informe Resumen (Vertical)"
            }[x],
            horizontal=True
        )
        
        if st.button("📥 Generar PDF", use_container_width=True):
            with st.spinner("Generando informe..."):
                # Obtener datos filtrados
                registros_filtrados = db.get_registros_fecha(
                    fecha_inicio.strftime("%Y-%m-%d"),
                    fecha_fin.strftime("%Y-%m-%d")
                )
                
                # Obtener estadísticas
                estadisticas = db.get_estadisticas_periodo(
                    fecha_inicio.strftime("%Y-%m-%d"),
                    fecha_fin.strftime("%Y-%m-%d")
                )
                
                # Generar PDF
                filename = generar_informe_pdf(
                    registros_filtrados,
                    estadisticas,
                    fecha_inicio.strftime("%d/%m/%Y"),
                    fecha_fin.strftime("%d/%m/%Y"),
                    tipo_informe
                )
                
                # Ofrecer descarga
                with open(filename, "rb") as f:
                    pdf_data = f.read()
                
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{filename}">📥 Haz clic aquí para descargar el PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("✅ PDF generado correctamente")
                
                # Limpiar archivo temporal
                os.remove(filename)
    else:
        st.info("No hay datos para generar informe")
    
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
