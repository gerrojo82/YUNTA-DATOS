import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from io import BytesIO

# Tema toggle - Inicialización
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Empieza en dark por default

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
st.set_page_config(
    page_title="YUNTA Intelligence - Pedidos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES DE FORMATO
# ============================================================================
def format_number(value):
    """Formato argentino para números: 1.234"""
    if pd.isna(value) or value == 0:
        return "0"
    if value == int(value):
        return f"{int(value):,}".replace(",", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_currency(value):
    """Formato moneda argentina: $ 1.234,56"""
    if pd.isna(value):
        return "$ 0,00"
    try:
        value = float(value)
        entero = int(abs(value))
        decimal = int((abs(value) - entero) * 100)
        entero_fmt = f"{entero:,}".replace(",", ".")
        sign = "-" if value < 0 else ""
        return f"{sign}$ {entero_fmt},{decimal:02d}"
    except:
        return "$ 0,00"

def clean_currency_to_float(value):
    """Limpia valores monetarios para cálculos numéricos"""
    if pd.isna(value):
        return 0.0
    try:
        str_val = str(value).strip()
        str_val = str_val.replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(str_val)
    except:
        return 0.0

def to_excel(df):
    """Genera archivo Excel descargable"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Pedidos')
    output.seek(0)
    return output

# ============================================================================
# ESTILOS CSS - Light / Dark (MAGENTA THEME)
# ============================================================================
dark_css = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

    .stApp { background: #1a1a2e !important; color: #e2e8f0 !important; }
    .block-container { padding: 2rem 3rem 6rem !important; max-width: 100% !important; }

    .main-header { 
        color: #e879f9 !important;
        font-size: 2.9rem !important; 
        font-weight: 900 !important; 
        letter-spacing: -0.5px;
        margin: 0.5rem 0;
    }
    .subtitle { color: #a1a1aa !important; font-size: 1.05rem !important; margin-bottom: 1.5rem; }

    .card {
        background: #252542 !important;
        border: 1px solid #3f3f5a !important;
        border-radius: 12px !important;
        padding: 1.6rem 1.2rem !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
        text-align: center;
    }
    .card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 30px rgba(232,121,249,0.15) !important;
        border-color: #e879f9 !important;
    }

    .metric-label { color: #e879f9 !important; font-size: 0.85rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
    .metric-value { font-size: clamp(1.6rem, 4vw, 2.4rem) !important; font-weight: 800 !important; color: #ffffff !important; line-height: 1.1 !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; max-width: 100% !important; }

    /* FIX KPIs en una sola línea */
    .row-widget.stHorizontal { flex-wrap: nowrap !important; overflow-x: auto !important; gap: 1.2rem !important; padding-bottom: 0.6rem !important; }
    [data-testid="column"] > div { min-width: 240px !important; flex-shrink: 0 !important; }

    /* Tablas */
    .stDataFrame { background: #252542 !important; border-radius: 12px !important; overflow: hidden; border: 1px solid #3f3f5a !important; }
    .stDataFrame [data-testid="stDataFrameResizable"] { background: #252542 !important; }
    .dataframe thead th { background: #1a1a2e !important; color: #e879f9 !important; font-weight: 600 !important; border-bottom: 2px solid #3f3f5a !important; }
    .dataframe tbody tr:hover { background: #2e2e4a !important; }
    .dataframe tbody td { color: #e2e8f0 !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #1a1a2e !important; border-right: 1px solid #3f3f5a !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3 { color: #e879f9 !important; }
    
    /* Botones */
    button[kind="primary"], .stButton > button, .stDownloadButton button { 
        background: linear-gradient(135deg, #c026d3, #e879f9) !important; 
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(232,121,249,0.3) !important;
    }
    button:hover, .stDownloadButton button:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 8px 24px rgba(232,121,249,0.45) !important; 
    }
    
    /* Inputs, selectbox, multiselect */
    .stSelectbox > div > div { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stMultiSelect > div > div { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stTextInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; border-radius: 10px !important; }
    .stNumberInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stDateInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    
    /* Labels de inputs */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stNumberInput label, .stDateInput label {
        color: #c4b5fd !important;
        font-weight: 500 !important;
    }
    
    /* Placeholders */
    ::placeholder { color: #6b7280 !important; opacity: 1 !important; }
    
    /* Radio buttons */
    .stRadio > div { color: #e2e8f0 !important; }
    .stRadio label { color: #e2e8f0 !important; }
    
    /* Markdown text */
    .stMarkdown p, .stMarkdown li { color: #e2e8f0 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #e879f9 !important; }
    
    /* Info boxes */
    .stAlert { border-radius: 8px !important; }

    hr { background: linear-gradient(90deg, transparent, #3f3f5a, transparent) !important; height: 1px !important; border: none !important; margin: 2.5rem 0 !important; }

    /* Scrollbar oscuro */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: #e879f9;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #c026d3;
    }
    
    /* Scrollbar en tablas */
    .stDataFrame ::-webkit-scrollbar-track {
        background: #252542;
    }
</style>"""

light_css = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

    .stApp { background: #fafafa !important; color: #1f2937 !important; }
    .block-container { padding: 2rem 3rem 6rem !important; max-width: 100% !important; }

    .main-header { 
        color: #be185d !important;
        font-size: 2.9rem !important; 
        font-weight: 900 !important; 
        letter-spacing: -0.5px;
        margin: 0.5rem 0;
    }
    .subtitle { color: #6b7280 !important; font-size: 1.05rem !important; margin-bottom: 1.5rem; }

    .card {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1.6rem 1.2rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        transition: all 0.3s ease !important;
        text-align: center;
    }
    .card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 24px rgba(190,24,93,0.12) !important;
        border-color: #f9a8d4 !important;
    }

    .metric-label { color: #be185d !important; font-size: 0.85rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
    .metric-value { font-size: clamp(1.6rem, 4vw, 2.4rem) !important; font-weight: 800 !important; color: #1f2937 !important; line-height: 1.1 !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; max-width: 100% !important; }

    /* FIX KPIs en una sola línea */
    .row-widget.stHorizontal { flex-wrap: nowrap !important; overflow-x: auto !important; gap: 1.2rem !important; padding-bottom: 0.6rem !important; }
    [data-testid="column"] > div { min-width: 240px !important; flex-shrink: 0 !important; }

    /* Tablas */
    .stDataFrame { background: white !important; border-radius: 12px !important; overflow: hidden; border: 1px solid #e5e7eb !important; }
    .stDataFrame [data-testid="stDataFrameResizable"] { background: white !important; }
    .dataframe thead th { background: #fdf2f8 !important; color: #be185d !important; font-weight: 600 !important; }
    .dataframe tbody tr:hover { background: #fdf2f8 !important; }
    .dataframe tbody td { color: #1f2937 !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e5e7eb !important; }
    [data-testid="stSidebar"] * { color: #1f2937 !important; }
    [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] .stMarkdown h2, [data-testid="stSidebar"] .stMarkdown h3 { color: #be185d !important; }
    
    /* Botones */
    button[kind="primary"], .stButton > button, .stDownloadButton button { 
        background: linear-gradient(135deg, #be185d, #ec4899) !important; 
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(190,24,93,0.2) !important;
    }
    button:hover, .stDownloadButton button:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 8px 24px rgba(190,24,93,0.35) !important; 
    }
    
    /* Inputs, selectbox, multiselect */
    .stSelectbox > div > div { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stMultiSelect > div > div { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stTextInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; border-radius: 10px !important; }
    .stNumberInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stDateInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    
    /* Labels de inputs */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stNumberInput label, .stDateInput label {
        color: #4b5563 !important;
        font-weight: 500 !important;
    }
    
    /* Placeholders */
    ::placeholder { color: #9ca3af !important; opacity: 1 !important; }
    
    /* Radio buttons */
    .stRadio > div { color: #1f2937 !important; }
    .stRadio label { color: #1f2937 !important; }
    
    /* Markdown text */
    .stMarkdown p, .stMarkdown li { color: #1f2937 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #be185d !important; }
    
    /* Info boxes */
    .stAlert { border-radius: 8px !important; }

    hr { background: linear-gradient(90deg, transparent, #e5e7eb, transparent) !important; height: 1px !important; border: none !important; margin: 2.5rem 0 !important; }

    /* Scrollbar claro */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: #be185d;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #9d174d;
    }
    
    /* Scrollbar en tablas */
    .stDataFrame ::-webkit-scrollbar-track {
        background: #fdf2f8;
    }
</style>"""

# Aplicar CSS según modo
if st.session_state.dark_mode:
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)

# ============================================================================
# CARGAR DATOS
# ============================================================================
@st.cache_data
def load_data():
    ruta = r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\pages\CONSOLIDADO_COMPLETO.parquet"
    try:
        df = pd.read_parquet(ruta)
        date_cols = ['Fecha_Pedido', 'Fecha_Recepcion', 'Fecha_Recepcion_Proveedor',
                     'Fecha_Primera_Transferencia', 'Fecha_Ultima_Transferencia']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        numeric_cols = ['Cantidad_Solicitada', 'Cantidad_Transferida_Entrada', 'Cantidad_Reasignada',
                        'Precio_Unitario', 'Precio_Real', 'Costo_Unitario_Transferencia',
                        'Precio_Total_Solicitado', 'Precio_Total_Transferido', 'Diferencia_Precio_Total']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Diferencia_Precio_Total' in df.columns:
            if df['Diferencia_Precio_Total'].dtype == 'object':
                df['Diferencia_Precio_Total'] = df['Diferencia_Precio_Total'].apply(clean_currency_to_float)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.error("❌ No se pudo cargar el archivo parquet")
    st.stop()

# ============================================================================
# SIDEBAR - FILTROS
# ============================================================================
st.sidebar.title("🔍 Filtros")

# Toggle de tema en sidebar
st.sidebar.markdown("### 🎨 Modo")
is_dark = st.sidebar.toggle("🌙 Oscuro / ☀️ Claro", value=st.session_state.dark_mode, key="theme_toggle_sidebar")

if is_dark != st.session_state.dark_mode:
    st.session_state.dark_mode = is_dark
    st.rerun()

st.sidebar.markdown("---")

# Fechas
st.sidebar.markdown("### 📅 Rango de Fechas")
tipo_fecha = st.sidebar.radio(
    "Filtrar por:",
    options=["Cualquier Fecha", "Fecha Pedido", "Fecha Recepción", "Fecha Transferencia"],
    index=0
)

if 'Fecha_Pedido' in df.columns:
    fechas_todas = []
    for col in ['Fecha_Pedido', 'Fecha_Recepcion', 'Fecha_Recepcion_Proveedor', 'Fecha_Primera_Transferencia']:
        if col in df.columns:
            fechas_todas.extend(df[col].dropna().tolist())
    if fechas_todas:
        fecha_min = min(fechas_todas).date()
        fecha_max = max(fechas_todas).date()
    else:
        fecha_min = date(2025, 1, 1)
        fecha_max = date.today()
else:
    fecha_min = date(2025, 1, 1)
    fecha_max = date.today()

col1, col2 = st.sidebar.columns(2)
with col1:
    fecha_desde = st.date_input("Desde", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
with col2:
    fecha_hasta = st.date_input("Hasta", value=fecha_max, min_value=fecha_min, max_value=fecha_max)

# Proveedor
st.sidebar.markdown("### 🏢 Proveedor")
proveedores = sorted(df['Proveedor'].dropna().unique())
proveedores_sel = st.sidebar.multiselect("Seleccionar Proveedores", options=proveedores, default=[])

# ID Pedido
ids_sel = []
if proveedores_sel:
    st.sidebar.markdown("### 📋 ID Pedido")
    df_prov = df[df['Proveedor'].isin(proveedores_sel)]
    ids_disponibles = sorted(df_prov['ID_Pedido'].dropna().unique())
    ids_sel = st.sidebar.multiselect("Seleccionar IDs", options=ids_disponibles, default=ids_disponibles)

# Tiendas
st.sidebar.markdown("### 🏪 Tiendas")
tiendas = sorted(df['Tienda'].dropna().unique())
tiendas_sel = st.sidebar.multiselect("Seleccionar Tiendas", options=tiendas, default=[])

# Estado
st.sidebar.markdown("### 📊 Estado Solicitud")
estados_sol = sorted(df['Estado_Solicitud'].dropna().unique())
estados_sol_sel = st.sidebar.multiselect("Seleccionar Estados", options=estados_sol, default=[])

# Búsqueda
st.sidebar.markdown("### 🔎 Búsqueda")
busqueda = st.sidebar.text_input("SKU o Descripción", "")

# ============================================================================
# APLICAR FILTROS
# ============================================================================
df_f = df.copy()

# Filtro de fecha
if 'Fecha_Pedido' in df_f.columns:
    if tipo_fecha == "Fecha Pedido":
        df_f = df_f[(df_f['Fecha_Pedido'].dt.date >= fecha_desde) & (df_f['Fecha_Pedido'].dt.date <= fecha_hasta)]
    elif tipo_fecha == "Fecha Recepción":
        df_f = df_f[(df_f['Fecha_Recepcion_Proveedor'].dt.date >= fecha_desde) & (df_f['Fecha_Recepcion_Proveedor'].dt.date <= fecha_hasta)]
    elif tipo_fecha == "Fecha Transferencia":
        df_f = df_f[(df_f['Fecha_Primera_Transferencia'].dt.date >= fecha_desde) & (df_f['Fecha_Primera_Transferencia'].dt.date <= fecha_hasta)]
    else:
        mask_fecha = (
            ((df_f['Fecha_Pedido'].notna()) & (df_f['Fecha_Pedido'].dt.date >= fecha_desde) & (df_f['Fecha_Pedido'].dt.date <= fecha_hasta)) |
            ((df_f['Fecha_Recepcion'].notna()) & (df_f['Fecha_Recepcion'].dt.date >= fecha_desde) & (df_f['Fecha_Recepcion'].dt.date <= fecha_hasta)) |
            ((df_f['Fecha_Recepcion_Proveedor'].notna()) & (df_f['Fecha_Recepcion_Proveedor'].dt.date >= fecha_desde) & (df_f['Fecha_Recepcion_Proveedor'].dt.date <= fecha_hasta)) |
            ((df_f['Fecha_Primera_Transferencia'].notna()) & (df_f['Fecha_Primera_Transferencia'].dt.date >= fecha_desde) & (df_f['Fecha_Primera_Transferencia'].dt.date <= fecha_hasta))
        )
        df_f = df_f[mask_fecha]

if proveedores_sel:
    df_f = df_f[df_f['Proveedor'].isin(proveedores_sel)]
if ids_sel:
    df_f = df_f[df_f['ID_Pedido'].isin(ids_sel)]
if tiendas_sel:
    df_f = df_f[df_f['Tienda'].isin(tiendas_sel)]
if estados_sol_sel:
    df_f = df_f[df_f['Estado_Solicitud'].isin(estados_sol_sel)]
if busqueda:
    mask = (df_f['SKU'].astype(str).str.contains(busqueda, case=False, na=False) |
            df_f['Descripcion'].astype(str).str.contains(busqueda, case=False, na=False))
    df_f = df_f[mask]

# ============================================================================
# TÍTULO PRINCIPAL
# ============================================================================
st.markdown('<h1 class="main-header">📦 YUNTA Intelligence - Pedidos</h1>', unsafe_allow_html=True)
st.markdown(
    f'<p class="subtitle">Control de Pedidos y Transferencias | '
    f'{fecha_desde.strftime("%d/%m/%Y")} - {fecha_hasta.strftime("%d/%m/%Y")} | '
    f'{len(df_f):,} registros</p>',
    unsafe_allow_html=True
)

st.markdown("---")

# ============================================================================
# RECÁLCULO DE MÉTRICAS
# ============================================================================
df_f['Fecha_Recepcion_Proveedor'] = pd.to_datetime(df_f['Fecha_Recepcion_Proveedor'], errors='coerce')
df_f['Fecha_Pedido'] = pd.to_datetime(df_f['Fecha_Pedido'], errors='coerce')
df_f['Fecha_Primera_Transferencia'] = pd.to_datetime(df_f['Fecha_Primera_Transferencia'], errors='coerce')
df_f['Base_Fecha_Calculo'] = df_f['Fecha_Recepcion_Proveedor'].combine_first(df_f['Fecha_Pedido'])
df_f['Dias_Hasta_Primera_Transferencia'] = df_f.apply(
    lambda row: 0 if pd.isna(row['Fecha_Primera_Transferencia']) or pd.isna(row['Base_Fecha_Calculo'])
                else max(0, (row['Fecha_Primera_Transferencia'] - row['Base_Fecha_Calculo']).days),
    axis=1
)
df_f['Porcentaje_Cumplimiento_Transferencia'] = np.where(
    (df_f['Cantidad_Reasignada'] > 0) & (df_f['Cantidad_Transferida_Entrada'].notna()),
    (df_f['Cantidad_Transferida_Entrada'] / df_f['Cantidad_Reasignada'] * 100).round(2),
    0
)

# ============================================================================
# KPIs
# ============================================================================
st.markdown("### 📊 KPIs Principales")

# Preparación de columnas auxiliares
if 'Cantidad_Reasignada' in df_f.columns and 'Cantidad_Transferida_Entrada' in df_f.columns:
    df_f['Dif_Unidades'] = df_f['Cantidad_Reasignada'].fillna(0) - df_f['Cantidad_Transferida_Entrada'].fillna(0)
else:
    df_f['Dif_Unidades'] = 0

if 'Costo_Unitario_Transferencia' in df_f.columns:
    df_f['Dif_Unidades_Valorizada'] = df_f['Dif_Unidades'] * df_f['Costo_Unitario_Transferencia'].fillna(0)
else:
    df_f['Dif_Unidades_Valorizada'] = 0

# Fila 1
col1, col2, col3 = st.columns(3)

total_transferido = (df_f['Cantidad_Transferida_Entrada'].fillna(0) * df_f['Costo_Unitario_Transferencia'].fillna(0)).sum()
col1.markdown(
    f'<div class="card"><div class="metric-label">TOTAL TRANSFERIDO</div>'
    f'<div class="metric-value">{format_currency(total_transferido)}</div></div>',
    unsafe_allow_html=True
)

total_pedido = (df_f['Cantidad_Reasignada'].fillna(0) * df_f['Precio_Unitario'].fillna(0)).sum()
col2.markdown(
    f'<div class="card"><div class="metric-label">TOTAL PEDIDO</div>'
    f'<div class="metric-value">{format_currency(total_pedido)}</div></div>',
    unsafe_allow_html=True
)

cumplimiento_promedio = df_f['Porcentaje_Cumplimiento_Transferencia'].mean()
col3.markdown(
    f'<div class="card"><div class="metric-label">% DE CUMPLIMIENTO</div>'
    f'<div class="metric-value">{cumplimiento_promedio:.1f}%</div></div>',
    unsafe_allow_html=True
)

# Fila 2
col4, col5, col6 = st.columns(3)

dif_unidades_val = df_f['Dif_Unidades_Valorizada'].sum()
color_dif_unidades = "#ef4444" if dif_unidades_val < 0 else "#10b981" if dif_unidades_val > 0 else "#ffffff"
col4.markdown(
    f'<div class="card"><div class="metric-label">DIF. UNIDADES VALORIZADA</div>'
    f'<div class="metric-value" style="color: {color_dif_unidades};">{format_currency(dif_unidades_val)}</div></div>',
    unsafe_allow_html=True
)

dif_precio_solo = 0
if all(col in df_f.columns for col in ['Precio_Unitario', 'Costo_Unitario_Transferencia', 'Cantidad_Reasignada']):
    mask_dif = df_f['Precio_Unitario'] != df_f['Costo_Unitario_Transferencia']
    dif_precio_solo = (df_f.loc[mask_dif, 'Precio_Unitario'].fillna(0) - df_f.loc[mask_dif, 'Costo_Unitario_Transferencia'].fillna(0)) * df_f.loc[mask_dif, 'Cantidad_Reasignada'].fillna(0)
    dif_precio_solo = dif_precio_solo.sum()
color_dif_precio_solo = "#ef4444" if dif_precio_solo < 0 else "#10b981" if dif_precio_solo > 0 else "#ffffff"
col5.markdown(
    f'<div class="card"><div class="metric-label">DIF. PRECIOS (solo líneas)</div>'
    f'<div class="metric-value" style="color: {color_dif_precio_solo};">{format_currency(dif_precio_solo)}</div></div>',
    unsafe_allow_html=True
)

dif_precio_total = df_f['Diferencia_Precio_Total'].sum() if 'Diferencia_Precio_Total' in df_f.columns else 0
color_dif_precio_total = "#ef4444" if dif_precio_total < 0 else "#10b981" if dif_precio_total > 0 else "#ffffff"
col6.markdown(
    f'<div class="card"><div class="metric-label">DIF. PRECIO TOTAL</div>'
    f'<div class="metric-value" style="color: {color_dif_precio_total};">{format_currency(dif_precio_total)}</div></div>',
    unsafe_allow_html=True
)

# ============================================================================
# TABLA
# ============================================================================
st.markdown("---")
st.markdown("### 📋 Detalle de Pedidos")

orden_deseado = [
    'ID_Pedido', 'SKU', 'Descripcion', 'Proveedor',
    'Fecha_Pedido', 'Fecha_Recepcion_Proveedor', 'Fecha_Primera_Transferencia', 'Dias_Hasta_Primera_Transferencia',
    'Cantidad_Solicitada', 'Cantidad_Reasignada', 'Cantidad_Transferida_Entrada',
    'Precio_Unitario', 'Costo_Unitario_Transferencia',
    'DIF. EN UNIDADES',
    'Precio_Total_Solicitado', 'Precio_Total_Transferido',
    'Dif. Unidades Valorizada',
    'Dif. Precios (solo líneas dif.)',
    'Diferencia_Precio_Total'
]

cols_existentes = [col for col in orden_deseado if col in df_f.columns]
df_show = df_f[cols_existentes].copy()

# DIF. EN UNIDADES
if 'Cantidad_Reasignada' in df_show.columns and 'Cantidad_Transferida_Entrada' in df_show.columns:
    if 'DIF. EN UNIDADES' not in df_show.columns:
        df_show['DIF. EN UNIDADES'] = df_show['Cantidad_Reasignada'].fillna(0) - df_show['Cantidad_Transferida_Entrada'].fillna(0)
        df_show['DIF. EN UNIDADES'] = df_show['DIF. EN UNIDADES'].apply(lambda x: format_number(x) if x != 0 else "0")

# Dif. Unidades Valorizada
if 'DIF. EN UNIDADES' in df_show.columns and 'Costo_Unitario_Transferencia' in df_show.columns:
    if 'Dif. Unidades Valorizada' not in df_show.columns:
        df_show['Dif_Unidades_Num'] = pd.to_numeric(
            df_show['DIF. EN UNIDADES'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        ).fillna(0)
        df_show['Dif. Unidades Valorizada'] = df_show['Dif_Unidades_Num'] * df_show['Costo_Unitario_Transferencia'].fillna(0)
        df_show['Dif. Unidades Valorizada'] = df_show['Dif. Unidades Valorizada'].apply(format_currency)
        df_show = df_show.drop(columns=['Dif_Unidades_Num'])

# Dif. Precios (solo líneas dif.)
if all(col in df_show.columns for col in ['Precio_Unitario', 'Costo_Unitario_Transferencia', 'Cantidad_Reasignada']):
    if 'Dif. Precios (solo líneas dif.)' not in df_show.columns:
        df_show['Dif. Precios (solo líneas dif.)'] = 0.0
        mask_dif = df_show['Precio_Unitario'] != df_show['Costo_Unitario_Transferencia']
        df_show.loc[mask_dif, 'Dif. Precios (solo líneas dif.)'] = (
            (df_show.loc[mask_dif, 'Precio_Unitario'].fillna(0) - df_show.loc[mask_dif, 'Costo_Unitario_Transferencia'].fillna(0)) *
            df_show.loc[mask_dif, 'Cantidad_Reasignada'].fillna(0)
        )
        df_show['Dif. Precios (solo líneas dif.)'] = df_show['Dif. Precios (solo líneas dif.)'].apply(format_currency)

# Formateo final
money_cols = ['Precio_Unitario', 'Costo_Unitario_Transferencia', 'Precio_Total_Solicitado', 'Precio_Total_Transferido', 'Diferencia_Precio_Total']
for col in money_cols:
    if col in df_show.columns:
        df_show[col] = df_show[col].apply(format_currency)

qty_cols = ['Cantidad_Solicitada', 'Cantidad_Reasignada', 'Cantidad_Transferida_Entrada']
for col in qty_cols:
    if col in df_show.columns:
        df_show[col] = df_show[col].apply(format_number)

orden_final_existentes = [col for col in orden_deseado if col in df_show.columns]
df_show = df_show[orden_final_existentes]
df_show = df_show.sort_values(by=['ID_Pedido', 'SKU'])

st.dataframe(df_show, use_container_width=True, height=600, hide_index=True)

# ============================================================================
# EXPORTAR
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Exportar")

if 'df_show' in locals() and not df_show.empty:
    export_df = df_show.copy()
    if 'Línea' in export_df.columns:
        export_df = export_df.drop(columns=['Línea'])

    excel_data = to_excel(export_df)

    st.sidebar.download_button(
        label="📥 Descargar Excel",
        data=excel_data,
        file_name=f"detalle_pedidos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_tabla_visible"
    )
else:
    st.sidebar.warning("No hay datos visibles para exportar.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información")
st.sidebar.info(f"""
**Total registros:** {len(df):,}
**Mostrados:** {len(df_f):,}
""")