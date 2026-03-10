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
                hora = st.time_input("Hora", datetime.now(BAIRES_TZ).time())
            
            concentracion = st.selectbox("Concentración (Color)", ["Amarillo", "Verde", "Rojo"])
            
            # Selector de unidad de peso
            unidad_peso = st.radio("Unidad de peso:", ["Kilogramos (kg)", "Gramos (g)"], horizontal=True)
            
            st.markdown("#### ⚖️ Pesos")
            
            # Factor de conversión: 1 kg = 1000 g
            factor = 1.0 if unidad_peso == "Kilogramos (kg)" else 0.001  # Si ingresa gramos, convertir a kg
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if unidad_peso == "Kilogramos (kg)":
                    peso_llena = st.number_input("Peso bolsa llena (infusión)", min_value=0.0, step=0.1, format="%.3f", value=2.0)
                    st.caption("Bolsa de solución NUEVA (kg)")
                else:
                    peso_llena_g = st.number_input("Peso bolsa llena (infusión)", min_value=0, step=10, format="%d", value=2000)
                    peso_llena = peso_llena_g / 1000
                    st.caption("Bolsa de solución NUEVA (g)")
            
            with col2:
                if unidad_peso == "Kilogramos (kg)":
                    peso_vacia = st.number_input("Peso bolsa vacía (opcional)", min_value=0.0, step=0.1, format="%.3f", value=0.0)
                    st.caption("Bolsa después de infundir (kg)")
                else:
                    peso_vacia_g = st.number_input("Peso bolsa vacía (opcional)", min_value=0, step=10, format="%d", value=0)
                    peso_vacia = peso_vacia_g / 1000
                    st.caption("Bolsa después de infundir (g)")
            
            with col3:
                if unidad_peso == "Kilogramos (kg)":
                    peso_drenaje = st.number_input("Peso bolsa drenaje", min_value=0.0, step=0.1, format="%.3f", value=2.2)
                    st.caption("Bolsa con líquido drenado (kg)")
                else:
                    peso_drenaje_g = st.number_input("Peso bolsa drenaje", min_value=0, step=10, format="%d", value=2200)
                    peso_drenaje = peso_drenaje_g / 1000
                    st.caption("Bolsa con líquido drenado (g)")
            
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

# Página: Ayuda Cicladora (nueva página)
if st.session_state.get("pagina") == "ayuda_cicladora":
    st.markdown("---")
    st.subheader("🤖 GUÍA PASO A PASO - CICLADORA BAXTER")
    
    # Inicializar el paso actual si no existe
    if "paso_cicladora" not in st.session_state:
        st.session_state.paso_cicladora = 1
    
    # Contenedor para el paso actual
    paso_container = st.container()
    
    with paso_container:
        if st.session_state.paso_cicladora == 1:
            st.markdown("### PASO 1: PREPARACIÓN INICIAL")
            st.markdown("""
            **1. Encender el equipo**  
            - Presiona el botón ubicado en la parte posterior del equipo  
            - Espera a que aparezca la leyenda en la pantalla
            
            **2. Iniciar programa**  
            - Presiona el botón verde "GO"  
            - Selecciona "Modo volumen pequeño" y presiona verde nuevamente
            """)
            
            if st.button("✅ HECHO - Continuar al Paso 2", use_container_width=True):
                st.session_state.paso_cicladora = 2
                st.rerun()
        
        elif st.session_state.paso_cicladora == 2:
            st.markdown("### PASO 2: COLOCAR EL CASSETTE")
            st.markdown("""
            **1. Preparar el cassette**  
            - Retira el envoltorio del cassette  
            - Levanta la manija para abrir la puerta del porta cassette  
            - Inserta el cassette (la parte blanda debe mirar hacia la máquina)  
            - Cierra la puerta bajando la palanca
            
            **2. Organizar líneas**  
            - Acomoda el organizador azul  
            - Cierra las 6 pinzas  
            - Coloca la línea de drenaje dentro del bidón vacío
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 1", use_container_width=True):
                    st.session_state.paso_cicladora = 1
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Continuar al Paso 3", use_container_width=True):
                    st.session_state.paso_cicladora = 3
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 3:
            st.markdown("### PASO 3: AUTOCOMPROBACIÓN")
            st.markdown("""
            **La máquina hará un test automático**  
            - Espera mientras la máquina se autocomprueba  
            - Mientras tanto, prepara tus manos para el siguiente paso  
            - Lávate las manos profundamente
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 2", use_container_width=True):
                    st.session_state.paso_cicladora = 2
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Continuar al Paso 4", use_container_width=True):
                    st.session_state.paso_cicladora = 4
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 4:
            st.markdown("### PASO 4: CONECTAR BOLSAS")
            st.markdown("""
            **1. Colocar pinzas**  
            - Coloca las pinzas azules en las bolsas  
            - Afloja la espiga del clamp rojo (bolsa superior)  
            - Afloja la espiga del clamp blanco (segunda bolsa, si usas dos)
            
            **2. Conectar**  
            - La espiga del clamp rojo va a la bolsa de arriba (calentada por la máquina)  
            - Sujeta la pinza, rompe la mariposa de la bolsa y conecta la espiga
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 3", use_container_width=True):
                    st.session_state.paso_cicladora = 3
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Continuar al Paso 5", use_container_width=True):
                    st.session_state.paso_cicladora = 5
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 5:
            st.markdown("### PASO 5: ABRIR PINZAS Y CEVAR")
            st.markdown("""
            **1. Abrir pinzas**  
            - Retira las pinzas azules  
            - Abre los clamp de las bolsas (rojo y blanco)  
            - Abre el clamp de la línea del paciente  
            - Presiona botón verde "CONTINUAR"
            
            **2. Cebado automático**  
            - La máquina purgará las tubuladuras automáticamente  
            - Espera a que termine
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 4", use_container_width=True):
                    st.session_state.paso_cicladora = 4
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Continuar al Paso 6", use_container_width=True):
                    st.session_state.paso_cicladora = 6
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 6:
            st.markdown("### PASO 6: CONEXIÓN AL PACIENTE")
            st.markdown("""
            **1. Preparar conexión**  
            - Cierra el clamp de la línea del paciente  
            - Limpia la zona de conexión con alcohol según indicación médica  
            - Procede a la conexión del catéter
            
            **2. Iniciar tratamiento**  
            - Abre el catéter y el clamp de la línea del paciente  
            - Presiona botón verde "CONTINUAR"  
            - Selecciona "Modo volumen pequeño" (NO continuar aún)
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 5", use_container_width=True):
                    st.session_state.paso_cicladora = 5
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Continuar al Paso 7", use_container_width=True):
                    st.session_state.paso_cicladora = 7
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 7:
            st.markdown("### PASO 7: VERIFICACIÓN INICIAL")
            st.markdown("""
            **Verificar drenaje inicial**  
            - La máquina mostrará "Verificar drenaje inicial"  
            - Aquí comienza el tratamiento  
            - La máquina hará ciclos de: infusión → permanencia → drenaje  
            - Esto tomará varias horas (puedes dormir)
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 6", use_container_width=True):
                    st.session_state.paso_cicladora = 6
                    st.rerun()
            with col2:
                if st.button("✅ COMPRENDIDO - Siguiente", use_container_width=True):
                    st.session_state.paso_cicladora = 8
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 8:
            st.markdown("### PASO 8: FIN DEL TRATAMIENTO (AL DESPERTAR)")
            st.markdown("""
            **1. Drenaje manual al despertar**  
            - Al despertar, la máquina mostrará "FIN DE TRATAMIENTO"  
            - Debes pararte para hacer un drenaje manual  
            - Presiona flecha hacia abajo hasta ver "DRENAJE MANUAL"  
            - Confirma con la flecha izquierda  
            - Espera a que termine el drenaje
            
            **2. Finalizar**  
            - Presiona botón verde "CONTINUAR"  
            - La máquina dirá "CIERRE CLAMP (TODOS)"  
            - Cierra clamp de línea paciente y catéter  
            - Presiona verde nuevamente
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 7", use_container_width=True):
                    st.session_state.paso_cicladora = 7
                    st.rerun()
            with col2:
                if st.button("✅ HECHO - Siguiente", use_container_width=True):
                    st.session_state.paso_cicladora = 9
                    st.rerun()
        
        elif st.session_state.paso_cicladora == 9:
            st.markdown("### PASO 9: DESCONEXIÓN Y REGISTRO")
            st.markdown("""
            **1. Desconectarse**  
            - La máquina dirá "DESCONECTESE"  
            - Realiza la limpieza según indicación médica  
            - Abre la tapa, coloca alcohol en gel  
            - Presiona verde para continuar  
            - La máquina dirá "DESCONECTEME" - ya puedes sacar el cassette
            
            **2. Registrar datos**  
            - Con la flecha hacia abajo, navega hasta ver los datos finales:  
              • Drenaje inicial  
              • Ultrafiltración total  
              • Tiempo medio de permanencia  
              • Tiempo perdido  
            - **ANOTA ESTOS VALORES** para registrarlos en la app  
            - Apaga el equipo con el botón posterior
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Volver al Paso 8", use_container_width=True):
                    st.session_state.paso_cicladora = 8
                    st.rerun()
            with col2:
                if st.button("🏁 FINALIZAR GUÍA", use_container_width=True):
                    st.session_state.paso_cicladora = 1
                    st.session_state.pagina = "principal"
                    st.rerun()
    
    # Botón para salir de la guía
    st.markdown("---")
    if st.button("❌ Cerrar guía", use_container_width=True):
        st.session_state.paso_cicladora = 1
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
            
            with st.form("form_modificar_manual"):
                st.markdown(f"### ✏️ Editando Registro Manual ID: {registro_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    fecha = st.date_input(
                        "Fecha", 
                        datetime.strptime(registro['fecha'], '%Y-%m-%d').date(),
                        format="DD/MM/YYYY"
                    )
                with col2:
                    hora = st.time_input(
                        "Hora",
                        datetime.strptime(registro['hora'], '%H:%M:%S').time()
                    )
                
                concentracion = st.selectbox(
                    "Concentración (Color)",
                    ["Amarillo", "Verde", "Rojo"],
                    index=["Amarillo", "Verde", "Rojo"].index(registro['concentracion'])
                )
                
                # Unidad de peso (recordar preferencia)
                unidad_peso = st.radio(
                    "Unidad de peso:",
                    ["Kilogramos (kg)", "Gramos (g)"],
                    horizontal=True
                )
                
                st.markdown("#### ⚖️ Pesos")
                
                # Mostrar valores actuales
                peso_llena_actual = float(registro['peso_bolsa_llena_kg'])
                peso_vacia_actual = float(registro['peso_bolsa_vacia_kg'] or 0)
                peso_drenaje_actual = float(registro['peso_bolsa_drenaje_kg'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if unidad_peso == "Kilogramos (kg)":
                        peso_llena = st.number_input(
                            "Peso bolsa llena (infusión)",
                            min_value=0.0, step=0.1, format="%.3f",
                            value=peso_llena_actual
                        )
                        st.caption(f"Actual: {peso_llena_actual:.3f} kg")
                    else:
                        peso_llena_g = st.number_input(
                            "Peso bolsa llena (infusión)",
                            min_value=0, step=10, format="%d",
                            value=int(peso_llena_actual * 1000)
                        )
                        peso_llena = peso_llena_g / 1000
                        st.caption(f"Actual: {int(peso_llena_actual * 1000)} g")
                
                with col2:
                    if unidad_peso == "Kilogramos (kg)":
                        peso_vacia = st.number_input(
                            "Peso bolsa vacía (opcional)",
                            min_value=0.0, step=0.1, format="%.3f",
                            value=peso_vacia_actual
                        )
                        st.caption(f"Actual: {peso_vacia_actual:.3f} kg")
                    else:
                        peso_vacia_g = st.number_input(
                            "Peso bolsa vacía (opcional)",
                            min_value=0, step=10, format="%d",
                            value=int(peso_vacia_actual * 1000)
                        )
                        peso_vacia = peso_vacia_g / 1000
                        st.caption(f"Actual: {int(peso_vacia_actual * 1000)} g")
                
                with col3:
                    if unidad_peso == "Kilogramos (kg)":
                        peso_drenaje = st.number_input(
                            "Peso bolsa drenaje",
                            min_value=0.0, step=0.1, format="%.3f",
                            value=peso_drenaje_actual
                        )
                        st.caption(f"Actual: {peso_drenaje_actual:.3f} kg")
                    else:
                        peso_drenaje_g = st.number_input(
                            "Peso bolsa drenaje",
                            min_value=0, step=10, format="%d",
                            value=int(peso_drenaje_actual * 1000)
                        )
                        peso_drenaje = peso_drenaje_g / 1000
                        st.caption(f"Actual: {int(peso_drenaje_actual * 1000)} g")
                
                # Mostrar volúmenes calculados
                if peso_llena > 0:
                    vol_infundido = (peso_llena - peso_vacia) * 1000
                    vol_drenado = peso_drenaje * 1000
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Volumen infundido",
                            f"{vol_infundido:.0f} ml",
                            delta=f"{vol_infundido - (registro['volumen_infundido_ml'] or 0):.0f}"
                        )
                    with col2:
                        st.metric(
                            "Volumen drenado",
                            f"{vol_drenado:.0f} ml",
                            delta=f"{vol_drenado - (registro['volumen_drenado_ml'] or 0):.0f}"
                        )
                
                observaciones = st.text_area(
                    "📝 Observaciones",
                    value=registro.get('observaciones', '')
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True):
                        # Obtener último registro manual para recalcular balance
                        ultimo = db.get_ultimo_registro_manual()
                        
                        # Calcular balance (usando el último registro como referencia)
                        if ultimo and ultimo['id'] != registro_id:
                            balance = (peso_drenaje * 1000) - ultimo.get('volumen_infundido_ml', 0)
                        else:
                            balance = (peso_drenaje * 1000) - (peso_llena - peso_vacia) * 1000
                        
                        datos_actualizados = {
                            'fecha': fecha.strftime("%Y-%m-%d"),
                            'hora': hora.strftime("%H:%M:%S"),
                            'concentracion': concentracion,
                            'peso_bolsa_llena_kg': peso_llena,
                            'peso_bolsa_vacia_kg': peso_vacia,
                            'peso_bolsa_drenaje_kg': peso_drenaje,
                            'balance_ml': balance,
                            'observaciones': observaciones
                        }
                        
                        try:
                            resultado = db.update_registro_manual(registro_id, datos_actualizados)
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
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state.modificar_paso = "seleccionar"
                        st.rerun()
        
        else:  # Cicladora
            # Obtener datos del registro de cicladora
            registro = db.get_registro_cicladora_by_id(registro_id)
            if not registro:
                st.error("No se encontró el registro")
                st.session_state.modificar_paso = "seleccionar"
                st.rerun()
            
            with st.form("form_modificar_cicladora"):
                st.markdown(f"### ✏️ Editando Registro Cicladora ID: {registro_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    fecha = st.date_input(
                        "Fecha",
                        datetime.strptime(registro['fecha'], '%Y-%m-%d').date(),
                        format="DD/MM/YYYY"
                    )
                with col2:
                    hora_inicio = st.time_input(
                        "Hora inicio",
                        datetime.strptime(registro['hora_inicio'], '%H:%M:%S').time()
                    )
                    hora_fin = st.time_input(
                        "Hora fin",
                        datetime.strptime(registro['hora_fin'], '%H:%M:%S').time()
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    drenaje_inicial = st.number_input(
                        "Vol. drenaje inicial (ml)",
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
                    volumen_solucion = st.number_input(
                        "Vol. total solución (ml)",
                        min_value=0, step=100,
                        value=registro.get('vol_total_solucion_ml', 0)
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
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True):
                        datos_actualizados = {
                            'fecha': fecha.strftime("%Y-%m-%d"),
                            'hora_inicio': hora_inicio.strftime("%H:%M:%S"),
                            'hora_fin': hora_fin.strftime("%H:%M:%S"),
                            'vol_drenaje_inicial_ml': drenaje_inicial,
                            'uf_total_cicladora_ml': uf_total,
                            'tiempo_permanencia_promedio_min': tiempo_permanencia,
                            'tiempo_perdido_min': tiempo_perdido,
                            'vol_total_solucion_ml': volumen_solucion,
                            'numero_ciclos_completados': num_ciclos,
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
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state.modificar_paso = "seleccionar"
                        st.rerun()
    
    # Botón para volver al menú (siempre visible)
    if st.button("← Volver al menú principal", use_container_width=True):
        st.session_state.modificar_paso = "seleccionar"
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
            hora = r.get('hora', '')[:5] if r.get('hora') else ''
            tipo = r['tipo_dialisis']
            
            # Calcular UF segun tipo
            if tipo == 'Cicladora':
                uf = r.get('uf_total_cicladora_ml', 0) or 0
            else:
                uf = r.get('uf_recambio_manual_ml', 0) or 0
            
            label = f"ID {r['id']} - {fecha} {hora} - {tipo} - UF: {uf:.0f} ml"
            opciones[label] = r['id']
        
        seleccion = st.selectbox("Selecciona registro a eliminar:", list(opciones.keys()))
        registro_id = opciones[seleccion]
        
        # Mostrar detalles del registro seleccionado
        st.warning(f"¿Estas seguro de eliminar el registro ID {registro_id}?")
        st.info("⚠️ Esta accion no se puede deshacer")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ CONFIRMAR ELIMINACION", type="primary", use_container_width=True):
                try:
                    # Obtener el registro para saber de qué tabla eliminar
                    registro_a_eliminar = next((r for r in registros if r['id'] == registro_id), None)
                    if registro_a_eliminar:
                        tabla = 'registros_manual' if registro_a_eliminar['tipo_dialisis'] == 'Manual' else 'registros_cicladora'
                        
                        # Eliminar de Supabase
                        response = db.supabase.table(tabla).delete().eq('id', registro_id).execute()
                        
                        if response.data:
                            st.success(f"✅ Registro ID {registro_id} eliminado correctamente")
                            st.balloons()
                            st.session_state.pagina = "principal"
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar el registro")
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
        with col2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.pagina = "principal"
                st.rerun()
    else:
        st.info("No hay registros para eliminar")
        if st.button("← Volver al menu"):
            st.session_state.pagina = "principal"
            st.rerun()
    
    if st.button("← Volver al menu"):
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
