import streamlit as st
# ============================================================
# VERIFICACIÓN DE CONEXIÓN (AGREGAR TEMPORALMENTE)
# ============================================================
import os
# st.write("🔍 Verificando variables de entorno:")
# st.write(f"SUPABASE_URL existe: {'SÍ' if os.getenv('SUPABASE_URL') else 'NO'}")
# st.write(f"SUPABASE_KEY existe: {'SÍ' if os.getenv('SUPABASE_KEY') else 'NO'}")

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
# Estilos CSS personalizados - MÁS CLARO Y LEGIBLE
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
    }
    .main-header {
        background: rgba(255, 255, 255, 0.98);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #fbcfe8;
    }
    .main-header h1 {
        color: #831843;
        font-size: 2.2rem !important;
    }
    .main-header h2 {
        color: #9d174d;
        font-size: 1.6rem !important;
    }
    .paciente-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border: 1px solid #fbcfe8;
    }
    .boton-menu {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        margin: 0.5rem 0;
        border: 2px solid #f9a8d4;
        width: 100%;
        font-size: 1.2rem !important;
        font-weight: bold;
        color: #831843;
    }
    .boton-menu:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(249, 168, 212, 0.3);
        background: #fdf2f8;
        border-color: #f472b6;
    }
    .ultimo-registro {
        background: #fdf2f8;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #ec4899;
        margin: 1rem 0;
        font-size: 1.1rem !important;
    }
    .footer {
        text-align: center;
        color: #831843;
        margin-top: 2rem;
        opacity: 0.9;
        font-size: 1rem !important;
    }
    /* Aumentar tamaño de fuente general */
    .stMarkdown, .stText, p, li, .stMetric label, .stMetric div {
        font-size: 1.1rem !important;
    }
    .stMetric .metric-value {
        font-size: 1.8rem !important;
    }
    .stButton button {
        font-size: 1.1rem !important;
        padding: 0.75rem 1rem !important;
    }
    .stSelectbox div[data-baseweb="select"] span {
        font-size: 1.1rem !important;
    }
    .stNumberInput input {
        font-size: 1.1rem !important;
    }
    .stDateInput input {
        font-size: 1.1rem !important;
    }
    .stTimeInput input {
        font-size: 1.1rem !important;
    }
    .stTextArea textarea {
        font-size: 1.1rem !important;
    }
    /* Tarjetas de métricas */
    div[data-testid="metric-container"] {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #fbcfe8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNCIÓN PARA TEXTO A VOZ (SIN API KEY)
# ============================================================
st.markdown("""
<script>
let vozHabilitada = false;
let vozFemenina = true;

function hablar(texto) {
    if (!vozHabilitada) return;
    
    // Cancelar cualquier síntesis en curso
    window.speechSynthesis.cancel();
    
    // Crear nuevo mensaje
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = 'es-ES';
    utterance.rate = 0.9;  // Velocidad
    utterance.pitch = 1;    // Tono
    utterance.volume = 1;   // Volumen
    
    // Seleccionar voz (femenina o masculina)
    const voces = window.speechSynthesis.getVoices();
    if (voces.length > 0) {
        if (vozFemenina) {
            // Buscar voz femenina en español
            const vozFem = voces.find(v => v.lang.includes('es') && v.name.includes('Female'));
            if (vozFem) utterance.voice = vozFem;
        } else {
            // Buscar voz masculina en español
            const vozMasc = voces.find(v => v.lang.includes('es') && v.name.includes('Male'));
            if (vozMasc) utterance.voice = vozMasc;
        }
    }
    
    window.speechSynthesis.speak(utterance);
}

function toggleVoz() {
    vozHabilitada = !vozHabilitada;
    const btn = document.getElementById('btn-voz');
    if (vozHabilitada) {
        btn.innerHTML = '🔊 VOZ ACTIVADA';
        btn.style.backgroundColor = '#ec4899';
        btn.style.color = 'white';
        hablar('Guía de voz activada');
    } else {
        btn.innerHTML = '🔇 ACTIVAR VOZ';
        btn.style.backgroundColor = '#f9a8d4';
        btn.style.color = '#831843';
        window.speechSynthesis.cancel();
    }
}

function cambiarVoz(tipo) {
    vozFemenina = (tipo === 'femenina');
    const btn = document.getElementById('btn-voz-fem');
    const btnMasc = document.getElementById('btn-voz-masc');
    if (tipo === 'femenina') {
        btn.style.backgroundColor = '#ec4899';
        btn.style.color = 'white';
        btnMasc.style.backgroundColor = '#f9a8d4';
        btnMasc.style.color = '#831843';
    } else {
        btnMasc.style.backgroundColor = '#ec4899';
        btnMasc.style.color = 'white';
        btn.style.backgroundColor = '#f9a8d4';
        btn.style.color = '#831843';
    }
    if (vozHabilitada) {
        hablar('Voz cambiada a ' + tipo);
    }
}
</script>

<style>
.voz-control {
    background: white;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border: 2px solid #f9a8d4;
    text-align: center;
}
.voz-btn {
    background: #f9a8d4;
    color: #831843;
    border: none;
    border-radius: 50px;
    padding: 10px 20px;
    margin: 5px;
    font-size: 1.1rem !important;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
}
.voz-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 5px 15px rgba(236, 72, 153, 0.3);
}
.voz-btn-activo {
    background: #ec4899;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Controles de voz en la barra lateral
with st.sidebar:
    st.markdown("### 🎤 Control de Voz")
    
    # Botón principal de voz
    st.components.v1.html("""
    <button id="btn-voz" class="voz-btn" style="width:100%;" onclick="toggleVoz()">
        🔊 ACTIVAR VOZ
    </button>
    """, height=50)
    
    # Selector de tipo de voz
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.components.v1.html("""
        <button id="btn-voz-fem" class="voz-btn" style="width:100%; background:#ec4899; color:white;" onclick="cambiarVoz('femenina')">
            👩 Femenina
        </button>
        """, height=50)
    with col_v2:
        st.components.v1.html("""
        <button id="btn-voz-masc" class="voz-btn" style="width:100%;" onclick="cambiarVoz('masculina')">
            👨 Masculina
        </button>
        """, height=50)
    
    st.markdown("---")


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
        
        # Determinar qué campo de hora usar
        if ultimo['tipo_dialisis'] == 'Manual':
            hora_mostrar = ultimo.get('hora', '')[:5] if ultimo.get('hora') else ''
        else:
            hora_mostrar = ultimo.get('hora_inicio', '')[:5] if ultimo.get('hora_inicio') else ''
        
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
                📅 {fecha.strftime('%d/%m/%Y')} {hora_mostrar}
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
    if st.button("🤖 GUÍA CICLADORA", use_container_width=True):  # <-- NUEVO BOTÓN
        st.session_state.pagina = "ayuda_cicladora"
        st.session_state.paso_cicladora = 1

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
                # Selector de hora tipo ruleta (nativo del celular)
                hora_time = st.time_input("Hora", datetime.now(BAIRES_TZ).time(), step=60)
                # Convertir a string para guardar
                hora_str = hora_time.strftime("%H:%M:%S")
            
            concentracion = st.selectbox("Concentración (Color)", ["Amarillo", "Verde", "Rojo"])
            
            # Selector de unidad de peso (fuera del form para que actualice inmediatamente)
            st.markdown("---")
            
            # Variable para almacenar valores en kg
            peso_llena_kg = 0
            peso_vacia_kg = 0
            peso_drenaje_kg = 0
            
            # Mostrar campos según unidad seleccionada
            if st.session_state.unidad_manual == "Kilogramos (kg)":
                st.markdown("#### ⚖️ Pesos (en kilogramos)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    peso_llena = st.number_input("Peso bolsa llena (infusión)", min_value=0.0, step=0.1, format="%.3f", value=2.0, key="peso_llena_kg")
                    peso_llena_kg = peso_llena
                    st.caption("Bolsa de solución NUEVA")
                with col2:
                    peso_vacia = st.number_input("Peso bolsa vacía (opcional)", min_value=0.0, step=0.1, format="%.3f", value=0.0, key="peso_vacia_kg")
                    peso_vacia_kg = peso_vacia
                    st.caption("Bolsa después de infundir")
                with col3:
                    peso_drenaje = st.number_input("Peso bolsa drenaje", min_value=0.0, step=0.1, format="%.3f", value=2.2, key="peso_drenaje_kg")
                    peso_drenaje_kg = peso_drenaje
                    st.caption("Bolsa con líquido drenado")
            else:  # Gramos
                st.markdown("#### ⚖️ Pesos (en gramos)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    peso_llena_g = st.number_input("Peso bolsa llena (infusión) (g)", min_value=0, step=10, format="%d", value=2000, key="peso_llena_g")
                    peso_llena_kg = peso_llena_g / 1000
                    st.caption(f"Equivale a {peso_llena_kg:.3f} kg")
                with col2:
                    peso_vacia_g = st.number_input("Peso bolsa vacía (opcional) (g)", min_value=0, step=10, format="%d", value=0, key="peso_vacia_g")
                    peso_vacia_kg = peso_vacia_g / 1000
                    st.caption(f"Equivale a {peso_vacia_kg:.3f} kg")
                with col3:
                    peso_drenaje_g = st.number_input("Peso bolsa drenaje (g)", min_value=0, step=10, format="%d", value=2200, key="peso_drenaje_g")
                    peso_drenaje_kg = peso_drenaje_g / 1000
                    st.caption(f"Equivale a {peso_drenaje_kg:.3f} kg")
            
            # Mostrar volúmenes calculados
            if peso_llena_kg > 0:
                vol_infundido = (peso_llena_kg - peso_vacia_kg) * 1000
                vol_drenado = peso_drenaje_kg * 1000
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Volumen infundido", f"{vol_infundido:.0f} ml")
                with col2:
                    st.metric("Volumen drenado", f"{vol_drenado:.0f} ml")
            
            observaciones = st.text_area("📝 Observaciones")
            
            if st.form_submit_button("💾 Guardar Registro Manual", use_container_width=True):
                datos = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'hora': hora_str,  # Usar hora_str en lugar de hora
                    'concentracion': concentracion,
                    'peso_llena': peso_llena_kg,
                    'peso_vacia': peso_vacia_kg,
                    'peso_drenaje': peso_drenaje_kg,
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
    
    else:  # Cicladora
        with st.form("form_cicladora"):
            st.markdown("### 🤖 Diálisis con Cicladora")
            st.info("Registra los datos que muestra la máquina al final del tratamiento")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.now(BAIRES_TZ), format="DD/MM/YYYY")
            with col2:
                # Esto es solo para mantener el layout
                st.markdown("")
            
            # Selectores de hora tipo ruleta (uno para inicio, otro para fin)
            st.markdown("#### ⏰ Horario del tratamiento")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                hora_inicio = st.time_input("Hora inicio", datetime.now(BAIRES_TZ).time(), step=60)
            with col_h2:
                hora_fin = st.time_input("Hora fin", (datetime.now(BAIRES_TZ) + timedelta(hours=8)).time(), step=60)
            
            # Convertir a string para guardar
            hora_inicio_str = hora_inicio.strftime("%H:%M:%S")
            hora_fin_str = hora_fin.strftime("%H:%M:%S")
            
            st.markdown("#### 🧴 BOLSAS UTILIZADAS")
            st.caption("La cicladora usa 2 bolsas. Selecciona los colores que utilizaste.")
            
            col1, col2 = st.columns(2)
            with col1:
                conc1 = st.selectbox("Color Bolsa 1", ["Amarillo", "Verde", "Rojo"], key="conc1")
            with col2:
                conc2 = st.selectbox("Color Bolsa 2", ["Amarillo", "Verde", "Rojo"], key="conc2")
            
            st.markdown("#### 📊 DATOS DE LA MÁQUINA (al finalizar)")
            st.caption("Anota los valores que muestra la pantalla de la cicladora")
            
            col1, col2 = st.columns(2)
            with col1:
                drenaje_inicial = st.number_input("Drenaje inicial (ml)", min_value=0, step=50, help="Volumen del primer drenaje")
                uf_total = st.number_input("UF Total (ml)", min_value=0, step=50, help="Ultrafiltración total del tratamiento")
                tiempo_permanencia = st.number_input("Tiempo permanencia promedio (min)", min_value=0, step=5)
            with col2:
                tiempo_perdido = st.number_input("Tiempo perdido (min)", min_value=0, step=5)
                num_ciclos = st.number_input("Número de ciclos", min_value=1, step=1, value=4)
            
            observaciones = st.text_area("📝 Observaciones")
            
            if st.form_submit_button("💾 Guardar Registro Cicladora", use_container_width=True):
                datos = {
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'hora_inicio': hora_inicio_str,
                    'hora_fin': hora_fin_str,
                    'drenaje_inicial': drenaje_inicial,
                    'uf_total': uf_total,
                    'tiempo_permanencia': tiempo_permanencia,
                    'tiempo_perdido': tiempo_perdido,
                    'num_ciclos': num_ciclos,
                    'concentracion1': conc1,
                    'concentracion2': conc2,
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

# Página: Ayuda Cicladora (nueva página)
# Página: Ayuda Cicladora (mejorada visualmente)
# Página: Ayuda Cicladora (con voz funcional usando gTTS)
if st.session_state.get("pagina") == "ayuda_cicladora":
    from gtts import gTTS
    import base64
    import tempfile
    
    # Función para generar audio y reproducirlo
    def generar_audio(texto, idioma='es', genero='femenino'):
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                # Generar audio con gTTS (siempre es femenino, pero es clara y natural)
                tts = gTTS(text=texto, lang=idioma, slow=False)
                tts.save(tmp.name)
                
                # Leer el archivo y codificarlo en base64
                with open(tmp.name, 'rb') as f:
                    audio_bytes = f.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                # Eliminar archivo temporal
                import os
                os.unlink(tmp.name)
                
                return f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
        except Exception as e:
            st.error(f"Error generando audio: {e}")
            return ""
    
    st.markdown("""
    <style>
    .paso-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        border-left: 8px solid #ec4899;
        box-shadow: 0 10px 25px rgba(236, 72, 153, 0.15);
    }
    .paso-titulo {
        color: #831843;
        font-size: 1.8rem !important;
        font-weight: bold;
        margin-bottom: 1.5rem;
    }
    .paso-contenido {
        color: #4a5568;
        line-height: 1.8;
        font-size: 1.2rem !important;
    }
    .numero-paso {
        background: #ec4899;
        color: white;
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: inline-block;
        text-align: center;
        line-height: 45px;
        margin-right: 15px;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .boton-paso {
        background: white;
        border: 2px solid #f9a8d4;
        border-radius: 50px;
        padding: 12px 20px;
        margin: 5px;
        font-size: 1.1rem !important;
        font-weight: bold;
        color: #831843;
        cursor: pointer;
        transition: all 0.3s;
        min-width: 90px;
    }
    .boton-paso:hover {
        background: #fdf2f8;
        border-color: #ec4899;
        transform: scale(1.05);
    }
    .voz-control {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border: 2px solid #f9a8d4;
        text-align: center;
    }
    .voz-btn {
        background: #f9a8d4;
        color: #831843;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        margin: 5px;
        font-size: 1.1rem !important;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s;
    }
    .voz-btn:hover {
        background: #ec4899;
        color: white;
        transform: scale(1.05);
    }
    .voz-btn-activo {
        background: #ec4899 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("## 🤖 GUÍA INTERACTIVA - CICLADORA BAXTER")
    
    # ============================================================
    # CONTROLES DE VOZ
    # ============================================================
    st.markdown("### 🎤 Control de Voz")
    
    # Inicializar estado de voz
    if "voz_activada" not in st.session_state:
        st.session_state.voz_activada = False
    
    col_v1, col_v2 = st.columns([1, 1])
    
    with col_v1:
        if st.button("🔊 ACTIVAR VOZ" if not st.session_state.voz_activada else "🔇 DESACTIVAR VOZ", 
                    use_container_width=True, type="primary" if st.session_state.voz_activada else "secondary"):
            st.session_state.voz_activada = not st.session_state.voz_activada
            if st.session_state.voz_activada:
                st.success("✅ Voz activada - Los pasos se reproducirán automáticamente")
            st.rerun()
    
    with col_v2:
        st.markdown("💬 **Idioma:** Español Latino (Google TTS)")
    
    st.markdown("---")
    
    # Inicializar paso
    if "paso_cicladora" not in st.session_state:
        st.session_state.paso_cicladora = 1
    
    # ============================================================
    # BOTONES DE NAVEGACIÓN RÁPIDA (PASOS 1-9)
    # ============================================================
    st.markdown("### 🔢 Saltar a paso:")
    
    pasos_titulos = [
        "1. Preparación", "2. Cassette", "3. Autocomprobación",
        "4. Conectar", "5. Cebado", "6. Conexión",
        "7. Inicio", "8. Despertar", "9. Registro"
    ]
    
    # Fila 1
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(pasos_titulos[0], key="paso1", use_container_width=True):
            st.session_state.paso_cicladora = 1
            st.rerun()
    with col2:
        if st.button(pasos_titulos[1], key="paso2", use_container_width=True):
            st.session_state.paso_cicladora = 2
            st.rerun()
    with col3:
        if st.button(pasos_titulos[2], key="paso3", use_container_width=True):
            st.session_state.paso_cicladora = 3
            st.rerun()
    
    # Fila 2
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(pasos_titulos[3], key="paso4", use_container_width=True):
            st.session_state.paso_cicladora = 4
            st.rerun()
    with col2:
        if st.button(pasos_titulos[4], key="paso5", use_container_width=True):
            st.session_state.paso_cicladora = 5
            st.rerun()
    with col3:
        if st.button(pasos_titulos[5], key="paso6", use_container_width=True):
            st.session_state.paso_cicladora = 6
            st.rerun()
    
    # Fila 3
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(pasos_titulos[6], key="paso7", use_container_width=True):
            st.session_state.paso_cicladora = 7
            st.rerun()
    with col2:
        if st.button(pasos_titulos[7], key="paso8", use_container_width=True):
            st.session_state.paso_cicladora = 8
            st.rerun()
    with col3:
        if st.button(pasos_titulos[8], key="paso9", use_container_width=True):
            st.session_state.paso_cicladora = 9
            st.rerun()
    
    st.markdown("---")
    
    # Barra de progreso
    progreso = (st.session_state.paso_cicladora) / 9
    st.progress(progreso, text=f"Paso {st.session_state.paso_cicladora} de 9")
    
    # ============================================================
    # PASO 1
    # ============================================================
    if st.session_state.paso_cicladora == 1:
        texto_paso1 = """Paso 1: Preparación inicial. Primero, enciende el equipo buscando el botón en la parte posterior de la máquina. Espera a que aparezca la pantalla de inicio. Luego presiona el botón verde GO. Finalmente selecciona Modo volumen pequeño y presiona verde nuevamente. La máquina está lista."""
        
        # Reproducir voz automáticamente si está activada
        if st.session_state.voz_activada and "ultimo_paso_hablado" not in st.session_state:
            st.session_state.ultimo_paso_hablado = 1
            audio_html = generar_audio(texto_paso1)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">1</span> ⚡ PREPARACIÓN INICIAL
            </div>
            <div class="paso-contenido">
                <p>🔌 <strong>Encender el equipo:</strong> Busca el botón en la parte POSTERIOR de la máquina y presiónalo.</p>
                <p>⏳ Espera a que aparezca la pantalla de inicio.</p>
                <p>✅ Presiona el botón verde <strong>"GO"</strong>.</p>
                <p>📏 Selecciona <strong>"Modo volumen pequeño"</strong> y presiona verde nuevamente.</p>
                <p style="color: #ec4899; font-weight: bold; font-size: 1.3rem;">✓ La máquina está lista</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 REPETIR PASO", use_container_width=True):
                audio_html = generar_audio(texto_paso1)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col2:
            if st.button("✅ PASO 2", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 2
                st.rerun()
    
    # ============================================================
    # PASO 2
    # ============================================================
    elif st.session_state.paso_cicladora == 2:
        texto_paso2 = """Paso 2: Colocar el cassette. Saca el cassette del envoltorio con cuidado. Levanta la manija para abrir la puerta del porta cassette. Inserta el cassette con la parte blanda hacia la máquina. Cierra la puerta bajando la palanca hasta que haga clic. Acomoda el organizador azul. Cierra las 6 pinzas. Coloca la línea de drenaje dentro del bidón vacío."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 2:
            st.session_state.ultimo_paso_hablado = 2
            audio_html = generar_audio(texto_paso2)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">2</span> 📦 COLOCAR EL CASSETTE
            </div>
            <div class="paso-contenido">
                <p>📎 <strong>Preparar cassette:</strong> Sácalo del envoltorio con cuidado.</p>
                <p>🔓 Levanta la manija para abrir la puerta del porta cassette.</p>
                <p>➡️ Inserta el cassette con la <strong>parte blanda hacia la máquina</strong>.</p>
                <p>🔒 Cierra la puerta bajando la palanca (debe hacer clic).</p>
                <p>🧩 Acomoda el organizador azul.</p>
                <p>📌 Cierra las 6 pinzas (todas).</p>
                <p>🗑️ Coloca la línea de drenaje dentro del bidón vacío.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 1", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 1
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso2)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 3", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 3
                st.rerun()
    
    # ============================================================
    # PASO 3
    # ============================================================
    elif st.session_state.paso_cicladora == 3:
        texto_paso3 = """Paso 3: Autocomprobación. La máquina hará un test automático. Espera unos segundos. Mientras tanto, lávate las manos profundamente por al menos 40 segundos. Prepara las bolsas para el siguiente paso. La máquina pitará cuando termine."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 3:
            st.session_state.ultimo_paso_hablado = 3
            audio_html = generar_audio(texto_paso3)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">3</span> 🔄 AUTOCOMPROBACIÓN
            </div>
            <div class="paso-contenido">
                <p>⏳ <strong>La máquina hará un test automático.</strong> Espera unos segundos.</p>
                <p>🧼 <strong>Mientras tanto:</strong> Lávate las manos profundamente (mínimo 40 segundos).</p>
                <p>✅ Prepara las bolsas para el siguiente paso.</p>
                <p>🔔 La máquina pitará cuando termine.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 2", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 2
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso3)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 4", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 4
                st.rerun()
    
    # ============================================================
    # PASO 4
    # ============================================================
    elif st.session_state.paso_cicladora == 4:
        texto_paso4 = """Paso 4: Conectar bolsas. Coloca las pinzas azules en las bolsas para sujetarlas. Afloja la espiga del clamp rojo que va a la bolsa superior que se calienta. Afloja la espiga del clamp blanco para la segunda bolsa si usas dos. Recuerda, la espiga del clamp rojo siempre va a la bolsa de arriba. Sujeta la pinza, rompe la mariposa de la bolsa y conecta la espiga."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 4:
            st.session_state.ultimo_paso_hablado = 4
            audio_html = generar_audio(texto_paso4)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">4</span> 🧴 CONECTAR BOLSAS
            </div>
            <div class="paso-contenido">
                <p>🔵 Coloca las pinzas azules en las bolsas (para sujetarlas).</p>
                <p>🔴 Afloja la espiga del clamp ROJO (bolsa superior - se calienta).</p>
                <p>⚪ Afloja la espiga del clamp BLANCO (segunda bolsa, si usas dos).</p>
                <p style="background: #fdf2f8; padding: 10px; border-radius: 8px; margin: 10px 0;">
                    <strong>💡 Importante:</strong> La espiga del clamp rojo SIEMPRE va a la bolsa de arriba 
                    (la que calienta la máquina).
                </p>
                <p>🖐️ Sujeta la pinza, rompe la mariposa de la bolsa y conecta la espiga.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 3", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 3
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso4)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 5", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 5
                st.rerun()
    
    # ============================================================
    # PASO 5
    # ============================================================
    elif st.session_state.paso_cicladora == 5:
        texto_paso5 = """Paso 5: Cebado de líneas. Retira las pinzas azules de las bolsas. Abre los clamp de las bolsas rojo y blanco. Abre el clamp de la línea del paciente. Presiona el botón verde continuar. La máquina purgará las tubuladuras automáticamente y verás burbujas."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 5:
            st.session_state.ultimo_paso_hablado = 5
            audio_html = generar_audio(texto_paso5)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">5</span> 💧 CEVADO DE LÍNEAS
            </div>
            <div class="paso-contenido">
                <p>🔓 Retira las pinzas azules de las bolsas.</p>
                <p>🚰 Abre los clamp de las bolsas (rojo y blanco).</p>
                <p>🩺 Abre el clamp de la línea del paciente.</p>
                <p>✅ Presiona botón verde <strong>"CONTINUAR"</strong>.</p>
                <p>⏳ La máquina purgará las tubuladuras automáticamente (verás burbujas).</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 4", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 4
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso5)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 6", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 6
                st.rerun()
    
    # ============================================================
    # PASO 6
    # ============================================================
    elif st.session_state.paso_cicladora == 6:
        texto_paso6 = """Paso 6: Conexión al paciente. Cierra el clamp de la línea del paciente. Limpia la zona de conexión con alcohol como te indicó el médico. Conecta el catéter del paciente a la línea. Abre el catéter y el clamp de la línea del paciente. Presiona el botón verde continuar. Luego selecciona Modo volumen pequeño pero no presiones continuar todavía."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 6:
            st.session_state.ultimo_paso_hablado = 6
            audio_html = generar_audio(texto_paso6)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">6</span> 👤 CONEXIÓN AL PACIENTE
            </div>
            <div class="paso-contenido">
                <p>🔒 Cierra el clamp de la línea del paciente.</p>
                <p>🧴 Limpia la zona de conexión con alcohol (como te indicó el médico).</p>
                <p>🔄 Conecta el catéter del paciente a la línea.</p>
                <p>🔓 Abre el catéter y el clamp de la línea del paciente.</p>
                <p>✅ Presiona botón verde <strong>"CONTINUAR"</strong>.</p>
                <p>📏 Selecciona <strong>"Modo volumen pequeño"</strong> (NO presiones continuar aún).</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 5", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 5
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso6)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 7", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 7
                st.rerun()
    
    # ============================================================
    # PASO 7
    # ============================================================
    elif st.session_state.paso_cicladora == 7:
        texto_paso7 = """Paso 7: Inicio del tratamiento. La máquina mostrará Verificar drenaje inicial. Verás el primer drenaje donde sale líquido del abdomen. Luego comenzarán los ciclos automáticos de infusión, permanencia y drenaje. Puedes dormir tranquilo, la máquina trabajará sola durante varias horas."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 7:
            st.session_state.ultimo_paso_hablado = 7
            audio_html = generar_audio(texto_paso7)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">7</span> 🌙 INICIO DEL TRATAMIENTO
            </div>
            <div class="paso-contenido">
                <p>🔍 La máquina mostrará <strong>"Verificar drenaje inicial"</strong>.</p>
                <p>⏳ Verás el primer drenaje (sale líquido del abdomen).</p>
                <p>🔄 Luego comenzarán los ciclos automáticos:</p>
                <p style="margin-left: 20px;">💧 INFUSIÓN → ⏱️ PERMANENCIA → 🚰 DRENAJE</p>
                <p>😴 <strong>Puedes dormir tranquilo.</strong> La máquina trabajará sola.</p>
                <p>⏰ El proceso tomará varias horas.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 6", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 6
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso7)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 8", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 8
                st.rerun()
    
    # ============================================================
    # PASO 8
    # ============================================================
    elif st.session_state.paso_cicladora == 8:
        texto_paso8 = """Paso 8: Al despertar. La máquina mostrará Fin de tratamiento. Presiona flecha hacia abajo hasta ver Drenaje manual. Confirma con la flecha izquierda. Espera a que termine el drenaje. Presiona botón verde continuar. La máquina dirá Cierre clamp todos. Cierra clamp de línea y catéter. Presiona verde nuevamente."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 8:
            st.session_state.ultimo_paso_hablado = 8
            audio_html = generar_audio(texto_paso8)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">8</span> 🌅 AL DESPERTAR
            </div>
            <div class="paso-contenido">
                <p>🔔 La máquina mostrará <strong>"FIN DE TRATAMIENTO"</strong>.</p>
                <p>⬇️ Presiona flecha hacia abajo hasta ver <strong>"DRENAJE MANUAL"</strong>.</p>
                <p>⬅️ Confirma con la flecha izquierda.</p>
                <p>⏳ Espera a que termine el drenaje.</p>
                <p>✅ Presiona botón verde <strong>"CONTINUAR"</strong>.</p>
                <p>🔒 La máquina dirá <strong>"CIERRE CLAMP (TODOS)"</strong>.</p>
                <p>🔒 Cierra clamp de línea y catéter.</p>
                <p>✅ Presiona verde nuevamente.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 7", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 7
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso8)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("✅ PASO 9", use_container_width=True, type="primary"):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 9
                st.rerun()
    
    # ============================================================
    # PASO 9
    # ============================================================
    elif st.session_state.paso_cicladora == 9:
        texto_paso9 = """Paso 9: Registro de datos. La máquina dirá Desconéctese. Limpia y aplica alcohol según indicación. Presiona verde para continuar. La máquina dirá Desconécteme. Ahora anota estos valores: Drenaje inicial, Ultrafiltración total, Tiempo medio de permanencia y Tiempo perdido. Apaga el equipo con el botón posterior. Tratamiento completado."""
        
        if st.session_state.voz_activada and st.session_state.get("ultimo_paso_hablado") != 9:
            st.session_state.ultimo_paso_hablado = 9
            audio_html = generar_audio(texto_paso9)
            st.markdown(audio_html, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="paso-card">
            <div class="paso-titulo">
                <span class="numero-paso">9</span> 📋 REGISTRO DE DATOS
            </div>
            <div class="paso-contenido">
                <p>🫱 La máquina dirá <strong>"DESCONECTESE"</strong>.</p>
                <p>🧴 Limpia y aplica alcohol según indicación.</p>
                <p>✅ Presiona verde para continuar.</p>
                <p>📤 La máquina dirá <strong>"DESCONECTEME"</strong>.</p>
                <p style="background: #fdf2f8; padding: 10px; border-radius: 8px; margin: 10px 0;">
                    <strong>📝 AHORA ANOTA ESTOS VALORES:</strong><br>
                    • 📊 Drenaje inicial: ______ ml<br>
                    • 💧 Ultrafiltración total: ______ ml<br>
                    • ⏱️ Tiempo medio de permanencia: ______ min<br>
                    • ⌛ Tiempo perdido: ______ min
                </p>
                <p>🔌 Apaga el equipo con el botón posterior.</p>
                <p>🎯 <strong>¡TRATAMIENTO COMPLETADO!</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ PASO 8", use_container_width=True):
                st.session_state.ultimo_paso_hablado = None
                st.session_state.paso_cicladora = 8
                st.rerun()
        with col2:
            if st.button("🔊 REPETIR", use_container_width=True):
                audio_html = generar_audio(texto_paso9)
                st.markdown(audio_html, unsafe_allow_html=True)
        with col3:
            if st.button("🏁 FINALIZAR", use_container_width=True, type="primary"):
                if st.session_state.voz_activada:
                    audio_html = generar_audio("¡Felicitaciones! Has completado la guía de cicladora. Buen tratamiento.")
                    st.markdown(audio_html, unsafe_allow_html=True)
                st.session_state.paso_cicladora = 1
                st.session_state.ultimo_paso_hablado = None
                st.session_state.pagina = "principal"
                st.rerun()
    
    # Botón para volver al menú
    if st.button("❌ Volver al menú principal", use_container_width=True):
        st.session_state.paso_cicladora = 1
        st.session_state.ultimo_paso_hablado = None
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



# Página: Modificar Registro
if st.session_state.pagina == "modificar":
    st.markdown("---")
    st.subheader("✏️ Modificar Registro")
    
    # Paso 1: Seleccionar registro
    if "modificar_paso" not in st.session_state:
        st.session_state.modificar_paso = "seleccionar"
        st.session_state.modificar_id = None
        st.session_state.modificar_tipo = None
    
    if st.session_state.modificar_paso == "seleccionar":
        registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
        if registros:
            # Crear opciones para el selector
            opciones = {}
            for r in registros[:20]:
                fecha = r['fecha'][-5:] if r['fecha'] else ''
                hora = r.get('hora', '')[:5] if r.get('hora') else ''
                if not hora and r.get('hora_inicio'):
                    hora = r.get('hora_inicio', '')[:5]
                tipo = r['tipo_dialisis']
                
                # Calcular UF según tipo
                if tipo == 'Cicladora':
                    uf = r.get('uf_total_cicladora_ml', 0) or 0
                else:
                    uf = r.get('uf_recambio_manual_ml', 0) or 0
                
                label = f"ID {r['id']} - {fecha} {hora} - {tipo} - UF: {uf:.0f} ml"
                opciones[label] = {'id': r['id'], 'tipo': r['tipo_dialisis']}
            
            seleccion = st.selectbox("Selecciona registro a modificar:", list(opciones.keys()))
            st.session_state.modificar_id = opciones[seleccion]['id']
            st.session_state.modificar_tipo = opciones[seleccion]['tipo']
            
            if st.button("✏️ CONTINUAR CON MODIFICACIÓN", use_container_width=True):
                st.session_state.modificar_paso = "editar"
                st.rerun()
        else:
            st.info("No hay registros para modificar")
            if st.button("← Volver al menú"):
                st.session_state.pagina = "principal"
                st.rerun()
    
    # Paso 2: Editar registro
    elif st.session_state.modificar_paso == "editar":
        registro_id = st.session_state.modificar_id
        tipo = st.session_state.modificar_tipo
        
        if tipo == "Manual":
            # Obtener datos del registro manual
            registro = db.get_registro_manual_by_id(registro_id)
            if not registro:
                st.error("No se encontró el registro")
                st.session_state.modificar_paso = "seleccionar"
                st.rerun()
            
            # Inicializar estado para unidad
            if "unidad_mod_manual" not in st.session_state:
                st.session_state.unidad_mod_manual = "Kilogramos (kg)"
            
            # Mostrar valores actuales
            st.markdown(f"### ✏️ Editando Registro Manual ID: {registro_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                nueva_fecha = st.date_input(
                    "Fecha", 
                    datetime.strptime(registro['fecha'], '%Y-%m-%d').date(),
                    format="DD/MM/YYYY"
                )
            with col2:
                # En Modificar Manual, reemplazar el selector de hora:
                nueva_hora_time = st.time_input(
                    "Hora",
                    datetime.strptime(registro['hora'], '%H:%M:%S').time(),
                    step=60
                )
                nueva_hora_str = nueva_hora_time.strftime("%H:%M:%S")

            nueva_concentracion = st.selectbox(
                "Concentración (Color)",
                ["Amarillo", "Verde", "Rojo"],
                index=["Amarillo", "Verde", "Rojo"].index(registro['concentracion'])
            )
            
            # Selector de unidad de peso (AL MISMO NIVEL que selectbox)
            st.session_state.unidad_mod_manual = st.radio(
                "Unidad de peso:",
                ["Kilogramos (kg)", "Gramos (g)"],
                horizontal=True,
                key="unidad_selector_mod"
            )
            
            # Valores actuales (AL MISMO NIVEL)
            peso_llena_actual = float(registro['peso_bolsa_llena_kg'])
            peso_vacia_actual = float(registro['peso_bolsa_vacia_kg'] or 0)
            peso_drenaje_actual = float(registro['peso_bolsa_drenaje_kg'])
            
            # Variables para almacenar valores modificados
            peso_llena_kg = peso_llena_actual
            peso_vacia_kg = peso_vacia_actual
            peso_drenaje_kg = peso_drenaje_actual
            
            # Mostrar campos según unidad
            if st.session_state.unidad_mod_manual == "Kilogramos (kg)":
                st.markdown("#### ⚖️ Pesos (en kilogramos)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    peso_llena = st.number_input(
                        "Peso bolsa llena (infusión)",
                        min_value=0.0, step=0.1, format="%.3f",
                        value=peso_llena_actual,
                        key="mod_peso_llena_kg"
                    )
                    peso_llena_kg = peso_llena
                    st.caption(f"Actual: {peso_llena_actual:.3f} kg")
                with col2:
                    peso_vacia = st.number_input(
                        "Peso bolsa vacía (opcional)",
                        min_value=0.0, step=0.1, format="%.3f",
                        value=peso_vacia_actual,
                        key="mod_peso_vacia_kg"
                    )
                    peso_vacia_kg = peso_vacia
                    st.caption(f"Actual: {peso_vacia_actual:.3f} kg")
                with col3:
                    peso_drenaje = st.number_input(
                        "Peso bolsa drenaje",
                        min_value=0.0, step=0.1, format="%.3f",
                        value=peso_drenaje_actual,
                        key="mod_peso_drenaje_kg"
                    )
                    peso_drenaje_kg = peso_drenaje
                    st.caption(f"Actual: {peso_drenaje_actual:.3f} kg")
            else:  # Gramos
                st.markdown("#### ⚖️ Pesos (en gramos)")
                col1, col2, col3 = st.columns(3)
                with col1:
                    peso_llena_g = st.number_input(
                        "Peso bolsa llena (infusión) (g)",
                        min_value=0, step=10, format="%d",
                        value=int(peso_llena_actual * 1000),
                        key="mod_peso_llena_g"
                    )
                    peso_llena_kg = peso_llena_g / 1000
                    st.caption(f"Actual: {int(peso_llena_actual * 1000)} g = {peso_llena_actual:.3f} kg")
                with col2:
                    peso_vacia_g = st.number_input(
                        "Peso bolsa vacía (opcional) (g)",
                        min_value=0, step=10, format="%d",
                        value=int(peso_vacia_actual * 1000),
                        key="mod_peso_vacia_g"
                    )
                    peso_vacia_kg = peso_vacia_g / 1000
                    st.caption(f"Actual: {int(peso_vacia_actual * 1000)} g = {peso_vacia_actual:.3f} kg")
                with col3:
                    peso_drenaje_g = st.number_input(
                        "Peso bolsa drenaje (g)",
                        min_value=0, step=10, format="%d",
                        value=int(peso_drenaje_actual * 1000),
                        key="mod_peso_drenaje_g"
                    )
                    peso_drenaje_kg = peso_drenaje_g / 1000
                    st.caption(f"Actual: {int(peso_drenaje_actual * 1000)} g = {peso_drenaje_actual:.3f} kg")
            
            # Mostrar volúmenes calculados (se actualizan en tiempo real)
            vol_infundido = (peso_llena_kg - peso_vacia_kg) * 1000
            vol_drenado = peso_drenaje_kg * 1000
            
            col1, col2 = st.columns(2)
            with col1:
                delta_inf = vol_infundido - (registro.get('volumen_infundido_ml', 0) or 0)
                st.metric(
                    "Volumen infundido",
                    f"{vol_infundido:.0f} ml",
                    delta=f"{delta_inf:.0f}"
                )
            with col2:
                delta_dren = vol_drenado - (registro.get('volumen_drenado_ml', 0) or 0)
                st.metric(
                    "Volumen drenado",
                    f"{vol_drenado:.0f} ml",
                    delta=f"{delta_dren:.0f}"
                )
            
            observaciones = st.text_area(
                "📝 Observaciones",
                value=registro.get('observaciones', '')
            )
            
            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
                    # Obtener último registro manual para recalcular balance
                    ultimo = db.get_ultimo_registro_manual()
                    
                    # Calcular balance
                    if ultimo and ultimo['id'] != registro_id:
                        balance = (peso_drenaje_kg * 1000) - ultimo.get('volumen_infundido_ml', 0)
                    else:
                        balance = (peso_drenaje_kg * 1000) - (peso_llena_kg - peso_vacia_kg) * 1000
                    
                    datos_actualizados = {
                        'fecha': nueva_fecha.strftime("%Y-%m-%d"),
                        'hora': nueva_hora.strftime("%H:%M:%S"),
                        'concentracion': nueva_concentracion,
                        'peso_bolsa_llena_kg': peso_llena_kg,
                        'peso_bolsa_vacia_kg': peso_vacia_kg,
                        'peso_bolsa_drenaje_kg': peso_drenaje_kg,
                        'balance_ml': balance,
                        'observaciones': observaciones
                    }
                    
                    print(f"Enviando datos para actualizar: {datos_actualizados}")  # Para debug
                    
                    try:
                        resultado = db.update_registro_manual(registro_id, datos_actualizados)
                        if resultado:
                            st.success("✅ Registro modificado correctamente")
                            st.balloons()
                            st.session_state.modificar_paso = "seleccionar"
                            st.session_state.pagina = "principal"
                            st.rerun()
                        else:
                            st.error("No se pudo actualizar el registro - Verifica que el ID existe")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.modificar_paso = "seleccionar"
                    st.rerun()
        
        else:  # Cicladora
            # Obtener datos del registro de cicladora
            registro = db.get_registro_cicladora_by_id(registro_id)
            if not registro:
                st.error("No se encontró el registro")
                st.session_state.modificar_paso = "seleccionar"
                st.rerun()
            
            st.markdown(f"### ✏️ Editando Registro Cicladora ID: {registro_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                nueva_fecha = st.date_input(
                    "Fecha",
                    datetime.strptime(registro['fecha'], '%Y-%m-%d').date(),
                    format="DD/MM/YYYY"
                )
            with col2:
                # En Modificar Cicladora
                hora_inicio_time = st.time_input(
                    "Hora inicio",
                    datetime.strptime(registro['hora_inicio'], '%H:%M:%S').time(),
                    step=60
                )
                hora_fin_time = st.time_input(
                    "Hora fin",
                    datetime.strptime(registro['hora_fin'], '%H:%M:%S').time(),
                    step=60
                )
                hora_inicio_str = hora_inicio_time.strftime("%H:%M:%S")
                hora_fin_str = hora_fin_time.strftime("%H:%M:%S")
            
            st.markdown("#### 🧴 BOLSAS UTILIZADAS")
            col1, col2 = st.columns(2)
            with col1:
                conc1 = st.selectbox(
                    "Color Bolsa 1",
                    ["Amarillo", "Verde", "Rojo"],
                    index=["Amarillo", "Verde", "Rojo"].index(registro.get('concentracion_bolsa1', 'Amarillo'))
                )
            with col2:
                conc2 = st.selectbox(
                    "Color Bolsa 2",
                    ["Amarillo", "Verde", "Rojo"],
                    index=["Amarillo", "Verde", "Rojo"].index(registro.get('concentracion_bolsa2', 'Amarillo'))
                )
            
            st.markdown("#### 📊 DATOS DE LA MÁQUINA")
            col1, col2 = st.columns(2)
            with col1:
                drenaje_inicial = st.number_input(
                    "Drenaje inicial (ml)",
                    min_value=0, step=50,
                    value=registro.get('vol_drenaje_inicial_ml', 0)
                )
                uf_total = st.number_input(
                    "UF Total (ml)",
                    min_value=0, step=50,
                    value=registro.get('uf_total_cicladora_ml', 0)
                )
                tiempo_permanencia = st.number_input(
                    "Tiempo permanencia promedio (min)",
                    min_value=0, step=5,
                    value=registro.get('tiempo_permanencia_promedio_min', 0)
                )
            with col2:
                tiempo_perdido = st.number_input(
                    "Tiempo perdido (min)",
                    min_value=0, step=5,
                    value=registro.get('tiempo_perdido_min', 0)
                )
                num_ciclos = st.number_input(
                    "Número de ciclos",
                    min_value=1, step=1,
                    value=registro.get('numero_ciclos_completados', 4)
                )
            
            observaciones = st.text_area(
                "📝 Observaciones",
                value=registro.get('observaciones', '')
            )
            
            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
                    datos_actualizados = {
                        'fecha': nueva_fecha.strftime("%Y-%m-%d"),
                        'hora_inicio': hora_inicio.strftime("%H:%M:%S"),
                        'hora_fin': hora_fin.strftime("%H:%M:%S"),
                        'vol_drenaje_inicial_ml': drenaje_inicial,
                        'uf_total_cicladora_ml': uf_total,
                        'tiempo_permanencia_promedio_min': tiempo_permanencia,
                        'tiempo_perdido_min': tiempo_perdido,
                        'numero_ciclos_completados': num_ciclos,
                        'concentracion_bolsa1': conc1,
                        'concentracion_bolsa2': conc2,
                        'observaciones': observaciones
                    }
                    
                    try:
                        resultado = db.update_registro_cicladora(registro_id, datos_actualizados)
                        if resultado:
                            st.success("✅ Registro modificado correctamente")
                            st.balloons()
                            st.session_state.modificar_paso = "seleccionar"
                            st.session_state.pagina = "principal"
                            st.rerun()
                        else:
                            st.error("No se pudo actualizar el registro")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.modificar_paso = "seleccionar"
                    st.rerun()
    else:
        st.info("No hay registros para eliminar")
        if st.button("← Volver al menu"):
            st.session_state.pagina = "principal"
            st.rerun()
    
    if st.button("← Volver al menu"):
        st.session_state.pagina = "principal"
        st.rerun()


# Página: Eliminar Registro
if st.session_state.pagina == "eliminar":
    st.markdown("---")
    st.subheader("🗑️ Eliminar Registro")
    
    registros = db.get_registros_fecha("2000-01-01", "2100-01-01")
    if registros:
        # Crear opciones para el selector
        opciones = {}
        for r in registros[:20]:
            fecha = r['fecha'][-5:] if r['fecha'] else ''
            if r['tipo_dialisis'] == 'Manual':
                hora = r.get('hora', '')[:5] if r.get('hora') else ''
            else:
                hora = r.get('hora_inicio', '')[:5] if r.get('hora_inicio') else ''
            
            tipo = r['tipo_dialisis']
            
            # Calcular UF según tipo
            if tipo == 'Cicladora':
                uf = r.get('uf_total_cicladora_ml', 0) or 0
            else:
                uf = r.get('uf_recambio_manual_ml', 0) or 0
            
            label = f"ID {r['id']} - {fecha} {hora} - {tipo} - UF: {uf:.0f} ml"
            opciones[label] = {'id': r['id'], 'tipo': r['tipo_dialisis']}
        
        seleccion = st.selectbox("Selecciona registro a eliminar:", list(opciones.keys()))
        registro_id = opciones[seleccion]['id']
        registro_tipo = opciones[seleccion]['tipo']
        
        # Mostrar detalles del registro seleccionado
        st.warning(f"¿Estás seguro de eliminar el registro ID {registro_id}?")
        st.info("⚠️ Esta acción no se puede deshacer")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ CONFIRMAR ELIMINACIÓN", type="primary", use_container_width=True):
                try:
                    # Determinar tabla según tipo
                    if registro_tipo == 'Manual':
                        tabla = 'registros_manual'
                    else:
                        tabla = 'registros_cicladora'
                    
                    # Eliminar de Supabase
                    response = db.supabase.table(tabla).delete().eq('id', registro_id).execute()
                    
                    if response.data:
                        st.success(f"✅ Registro ID {registro_id} eliminado correctamente")
                        st.balloons()
                        st.session_state.pagina = "principal"
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar el registro - Verifica que el ID existe")
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.pagina = "principal"
                st.rerun()
    else:
        st.info("No hay registros para eliminar")
        if st.button("← Volver al menú"):
            st.session_state.pagina = "principal"
            st.rerun()
    
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
