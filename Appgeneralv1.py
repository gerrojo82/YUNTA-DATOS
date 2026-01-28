import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import duckdb
from pathlib import Path
import requests
import json

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
st.set_page_config(
    page_title="YUNTA Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CARGAR DATOS DESDE HUGGING FACE (reemplaza Google Drive)
# ============================================================================
from datasets import load_dataset

@st.cache_data(ttl=86400, show_spinner="📥 Cargando datos completos desde Hugging Face... (rápido y sin límites)")
def cargar_datos():
    """Carga los datos consolidados y movimientos desde Hugging Face"""
    try:
        df_consolidado = load_dataset(
            "gerrojo82/yunta-dashboad-datos",   # tu repo exacto
            "consolidado",
            split="train"
        ).to_pandas()

        df_movimientos = load_dataset(
            "gerrojo82/yunta-dashboad-datos",
            "movimientos",
            split="train"
        ).to_pandas()

        st.success("Datos cargados exitosamente desde Hugging Face!")
        return df_consolidado, df_movimientos

    except Exception as e:
        st.error(f"Error al cargar desde Hugging Face: {str(e)}")
        st.info("Verifica que el repo sea público o que tu token esté configurado si es privado.")
        raise e
    """Carga los datos desde Google Drive o local según disponibilidad"""
    
    # Rutas locales
    ruta_consolidado_local = Path(r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\pages\CONSOLIDADO_COMPLETO.parquet")
    ruta_movimientos_local = Path(r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\MOVIMIENTOS_STOCK_PowerBI.parquet")
    
    # Intentar cargar local primero (más rápido para desarrollo)
    if ruta_consolidado_local.exists() and ruta_movimientos_local.exists():
        df_consolidado = pd.read_parquet(ruta_consolidado_local)
        df_movimientos = pd.read_parquet(ruta_movimientos_local)
    else:
        # Cargar desde Google Drive (para Streamlit Cloud)
        with st.spinner("📥 Cargando datos desde la nube..."):
            df_consolidado = cargar_parquet_desde_drive(CONSOLIDADO_ID)
            df_movimientos = cargar_parquet_desde_drive(MOVIMIENTOS_ID)
    
    return df_consolidado, df_movimientos
# ============================================================================
# 🔐 MÓDULO DE LOGIN - Agregar al INICIO de Appgeneralv1.py
# ============================================================================
# Poner esto DESPUÉS de st.set_page_config() y ANTES de todo lo demás
# ============================================================================

import json

# ============================================================================
# CONFIGURACIÓN DE USUARIOS
# ============================================================================
def get_usuarios():
    """
    Obtiene usuarios desde JSON (desarrollo local) o Streamlit Secrets (producción)
    """
    # Primero intentar JSON local (desarrollo)
    json_path = Path("usuarios.json")
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Si no hay JSON, intentar Streamlit Secrets (producción)
    try:
        if "usuarios" in st.secrets:
            usuarios = {}
            for user_key in st.secrets["usuarios"]:
                user_data = st.secrets["usuarios"][user_key]
                usuarios[user_key] = {
                    "password": user_data["password"],
                    "nombre": user_data["nombre"],
                    "tiendas": list(user_data["tiendas"]),
                    "pantallas": list(user_data["pantallas"])
                }
            return usuarios
    except FileNotFoundError:
        pass
    
    # Si no existe nada, usuarios por defecto
    return {
        "admin": {
            "password": "admin123",
            "nombre": "Administrador",
            "tiendas": ["TODAS"],
            "pantallas": ["TODAS"]
        }
    }
# ============================================================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================================================
def verificar_login(usuario, password):
    """Verifica credenciales y retorna datos del usuario o None"""
    usuarios = get_usuarios()
    if usuario in usuarios and usuarios[usuario]["password"] == password:
        return {
            "usuario": usuario,
            "nombre": usuarios[usuario]["nombre"],
            "tiendas": usuarios[usuario]["tiendas"],
            "pantallas": usuarios[usuario]["pantallas"]
        }
    return None

def tiene_acceso_tienda(tienda, tiendas_permitidas):
    """Verifica si el usuario tiene acceso a una tienda"""
    if "TODAS" in tiendas_permitidas:
        return True
    return tienda in tiendas_permitidas

def tiene_acceso_pantalla(pantalla, pantallas_permitidas):
    """Verifica si el usuario tiene acceso a una pantalla"""
    if "TODAS" in pantallas_permitidas:
        return True
    return pantalla in pantallas_permitidas

def filtrar_tiendas(todas_tiendas, tiendas_permitidas):
    """Filtra la lista de tiendas según permisos del usuario"""
    if "TODAS" in tiendas_permitidas:
        return todas_tiendas
    return [t for t in todas_tiendas if t in tiendas_permitidas]

def filtrar_pantallas(todas_pantallas, pantallas_permitidas):
    """Filtra la lista de pantallas según permisos del usuario"""
    if "TODAS" in pantallas_permitidas:
        return todas_pantallas
    return [p for p in todas_pantallas if p in pantallas_permitidas]

# ============================================================================
# CSS PARA PANTALLA DE LOGIN
# ============================================================================
login_css = """
<style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: #252542;
        border-radius: 20px;
        border: 1px solid #3f3f5a;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .login-logo {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    .login-title {
        color: #e879f9;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
    }
    .login-subtitle {
        color: #a1a1aa;
        font-size: 0.95rem;
        margin-top: 5px;
    }
    .login-error {
        background: #451a2e;
        border: 1px solid #ef4444;
        color: #fca5a5;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
    }
    .login-footer {
        text-align: center;
        margin-top: 30px;
        color: #6b7280;
        font-size: 0.85rem;
    }
    .user-badge {
        background: linear-gradient(135deg, #c026d3, #e879f9);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
"""

# ============================================================================
# INICIALIZAR SESSION STATE PARA LOGIN
# ============================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# ============================================================================
# PANTALLA DE LOGIN
# ============================================================================
def mostrar_login():
    """Muestra la pantalla de login"""
    
    # Ocultar sidebar y navegación en login
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebarNavItems"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        .css-1d391kg { display: none !important; }
        .css-1cypcdb { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Aplicar CSS de login
    st.markdown(login_css, unsafe_allow_html=True)
    
    # Contenedor centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-header">
            <div class="login-logo">🔐</div>
            <h1 class="login-title">YUNTA Intelligence</h1>
            <p class="login-subtitle">Ingresá tus credenciales para continuar</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar error si existe
        if "login_error" in st.session_state and st.session_state.login_error:
            st.markdown(f'<div class="login-error">❌ {st.session_state.login_error}</div>', unsafe_allow_html=True)
        
        # Formulario de login
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario", placeholder="Ingresá tu usuario")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresá tu contraseña")
            
            submitted = st.form_submit_button("🚀 Ingresar", use_container_width=True)
            
            if submitted:
                if not usuario or not password:
                    st.session_state.login_error = "Completá usuario y contraseña"
                    st.rerun()
                else:
                    user_data = verificar_login(usuario, password)
                    if user_data:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_data
                        st.session_state.login_error = None
                        st.rerun()
                    else:
                        st.session_state.login_error = "Usuario o contraseña incorrectos"
                        st.rerun()
        
        st.markdown("""
        <div class="login-footer">
            La Yunta © 2025 - Business Intelligence
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# FUNCIÓN DE LOGOUT
# ============================================================================
def logout():
    """Cierra la sesión del usuario"""
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.login_error = None
    st.rerun()

# ============================================================================
# VERIFICAR SI ESTÁ LOGUEADO - PONER ESTO ANTES DE TODO EL CONTENIDO
# ============================================================================
if not st.session_state.logged_in:
    mostrar_login()
    st.stop()  # Detiene la ejecución aquí si no está logueado

# ============================================================================
# SI LLEGAMOS ACÁ, EL USUARIO ESTÁ LOGUEADO
# ============================================================================
# Obtener datos del usuario actual
usuario_actual = st.session_state.user_data
tiendas_usuario = usuario_actual["tiendas"]
pantallas_usuario = usuario_actual["pantallas"]

# ============================================================================
# MODO OSCURO/CLARO GLOBAL - Toggle en el SIDEBAR superior (siempre visible)
# ============================================================================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True  # Empieza en oscuro

# Toggle en el sidebar (arriba de todo)
with st.sidebar:
    st.markdown("### 🎨 Modo")
    is_dark = st.toggle("🌙 Oscuro / ☀️ Claro", value=st.session_state.dark_mode, key="global_dark_mode_toggle")

# Si cambió → recargar la app completa
if is_dark != st.session_state.dark_mode:
    st.session_state.dark_mode = is_dark
    st.rerun()

# ============================================================================
# CSS GLOBAL - se aplica en TODAS las páginas
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
    .stDataFrame { background: #252542 !important; border-radius: 12px !important; overflow: hidden; }
    .stDataFrame [data-testid="stDataFrameResizable"] { background: #252542 !important; }
    .dataframe thead th { background: #1a1a2e !important; color: #e879f9 !important; font-weight: 600 !important; border-bottom: 2px solid #3f3f5a !important; }
    .dataframe tbody tr:hover { background: #2e2e4a !important; }
    .dataframe tbody td { color: #e2e8f0 !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #1a1a2e !important; border-right: 1px solid #3f3f5a !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #e879f9 !important; }
    
    /* Botones */
    button[kind="primary"], .stButton > button { 
        background: linear-gradient(135deg, #c026d3, #e879f9) !important; 
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #a21caf, #d946ef) !important;
    }
    
    /* Inputs, selectbox, multiselect */
    .stSelectbox > div > div { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stMultiSelect > div > div { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stTextInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stNumberInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    .stDateInput > div > div > input { background: #252542 !important; border-color: #3f3f5a !important; color: #e2e8f0 !important; }
    
    /* Labels de inputs */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stNumberInput label, .stDateInput label {
        color: #c4b5fd !important;
        font-weight: 500 !important;
    }
    
    /* Placeholders */
    ::placeholder { color: #6b7280 !important; opacity: 1 !important; }
    
    /* Expanders */
    .streamlit-expanderHeader { background: #252542 !important; border-radius: 8px !important; color: #e2e8f0 !important; }
    .streamlit-expanderContent { background: #1e1e38 !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #252542 !important; border-radius: 8px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa !important; background: transparent !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #c026d3, #e879f9) !important; color: white !important; border-radius: 6px; }
    
    /* Radio buttons */
    .stRadio > div { color: #e2e8f0 !important; }
    .stRadio label { color: #e2e8f0 !important; }
    
    /* Checkbox */
    .stCheckbox label { color: #e2e8f0 !important; }
    
    /* Sliders */
    .stSlider label { color: #c4b5fd !important; }
    .stSlider [data-baseweb="slider"] { background: #3f3f5a !important; }
    
    /* Markdown text */
    .stMarkdown p, .stMarkdown li { color: #e2e8f0 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #e879f9 !important; }
    
    /* Info, warning, error, success boxes */
    .stAlert { border-radius: 8px !important; }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: #252542 !important;
        border: 1px solid #e879f9 !important;
        color: #e879f9 !important;
    }
    .stDownloadButton > button:hover {
        background: #e879f9 !important;
        color: #1a1a2e !important;
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
    [data-testid="stSidebar"] .stMarkdown h3 { color: #be185d !important; }
    
    /* Botones */
    button[kind="primary"], .stButton > button { 
        background: linear-gradient(135deg, #be185d, #ec4899) !important; 
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #9d174d, #db2777) !important;
    }
    
    /* Inputs, selectbox, multiselect */
    .stSelectbox > div > div { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stMultiSelect > div > div { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stTextInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stNumberInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    .stDateInput > div > div > input { background: white !important; border-color: #d1d5db !important; color: #1f2937 !important; }
    
    /* Labels de inputs */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stNumberInput label, .stDateInput label {
        color: #4b5563 !important;
        font-weight: 500 !important;
    }
    
    /* Placeholders */
    ::placeholder { color: #9ca3af !important; opacity: 1 !important; }
    
    /* Expanders */
    .streamlit-expanderHeader { background: white !important; border: 1px solid #e5e7eb !important; border-radius: 8px !important; color: #1f2937 !important; }
    .streamlit-expanderContent { background: #fafafa !important; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: white !important; border-radius: 8px; border: 1px solid #e5e7eb; gap: 4px; }
    .stTabs [data-baseweb="tab"] { color: #6b7280 !important; background: transparent !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #be185d, #ec4899) !important; color: white !important; border-radius: 6px; }
    
    /* Radio buttons */
    .stRadio > div { color: #1f2937 !important; }
    .stRadio label { color: #1f2937 !important; }
    
    /* Checkbox */
    .stCheckbox label { color: #1f2937 !important; }
    
    /* Sliders */
    .stSlider label { color: #4b5563 !important; }
    
    /* Markdown text */
    .stMarkdown p, .stMarkdown li { color: #1f2937 !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #be185d !important; }
    
    /* Info, warning, error, success boxes */
    .stAlert { border-radius: 8px !important; }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: white !important;
        border: 1px solid #be185d !important;
        color: #be185d !important;
    }
    .stDownloadButton > button:hover {
        background: #be185d !important;
        color: white !important;
    }
</style>"""

# Aplicar CSS en TODAS las páginas
if st.session_state.dark_mode:
    st.markdown(dark_css, unsafe_allow_html=True)
else:
    st.markdown(light_css, unsafe_allow_html=True)
# ==========================================================================
# FUNCIONES DE FORMATO
# ==========================================================================
def format_number(value):
    try:
        if pd.isna(value) or float(value) == 0:
            return "0"
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return "0"

def format_currency(value):
    try:
        if pd.isna(value) or float(value) == 0:
            return "$ 0,00"
        v = float(value)
        entero = int(v)
        decimal = int(round((v - entero) * 100))
        if decimal == 100:
            entero += 1
            decimal = 0
        entero_fmt = f"{entero:,}".replace(",", ".")
        return f"$ {entero_fmt},{decimal:02d}"
    except Exception:
        return "$ 0,00"

def format_percent(value):
    try:
        if pd.isna(value):
            return "0,0%"
        return f"{float(value):.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"

# ==========================================================================
# EXPORTAR A EXCEL
# ==========================================================================
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        wb = writer.book
        if 'Reporte' not in wb.sheetnames:
            wb.create_sheet('Reporte')
        ws = wb['Reporte']
        ws.sheet_state = 'visible'

        if df is None or getattr(df, 'empty', False):
            ws.append(["Sin datos"])
        else:
            max_rows = 1048576
            total_rows = len(df)
            if total_rows <= max_rows:
                df.to_excel(writer, index=False, sheet_name='Reporte')
            else:
                chunks = (total_rows // max_rows) + 1
                for i in range(chunks):
                    start = i * max_rows
                    end = min((i + 1) * max_rows, total_rows)
                    sheet_name = f"Reporte_{i+1}"
                    df.iloc[start:end].to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output

# ==========================================================================
# CARGAR DATOS (Local o Google Drive)
# ==========================================================================
import tempfile

BASE_DIR = Path(__file__).resolve().parent

# Rutas locales (solo funcionan en tu PC)
PARQUET_PATH_LOCAL = Path(r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\MOVIMIENTOS_STOCK_PowerBI.parquet")
PARQUET_PATH_REPO = BASE_DIR / "MOVIMIENTOS_STOCK_PowerBI.parquet"

# Determinar origen de datos
PARQUET_PATH = None

if PARQUET_PATH_LOCAL.exists():
    # LOCAL: usar archivo directo (tu PC)
    PARQUET_PATH = str(PARQUET_PATH_LOCAL)
elif PARQUET_PATH_REPO.exists() and PARQUET_PATH_REPO.stat().st_size > 1024:
    # REPO: archivo en el repositorio
    PARQUET_PATH = str(PARQUET_PATH_REPO)
else:
    # NUBE: descargar de Google Drive
    try:
        with st.spinner("📥 Descargando datos desde Google Drive..."):
            df_movimientos_drive = cargar_parquet_desde_drive(MOVIMIENTOS_ID)
            # Guardar temporalmente para DuckDB
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.parquet')
            df_movimientos_drive.to_parquet(temp_file.name)
            PARQUET_PATH = temp_file.name
    except Exception as e:
        st.error(f"❌ Error al descargar de Google Drive: {e}")
        st.stop()

if PARQUET_PATH is None:
    st.error("❌ No se pudo cargar el archivo de datos")
    st.stop()

@st.cache_resource
def get_con():
    con = duckdb.connect(database=":memory:")
    con.execute(f"CREATE VIEW movimientos AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
    return con

con = get_con()

@st.cache_data(ttl=3600)
def get_schema_cols():
    df = con.execute("DESCRIBE SELECT * FROM movimientos").df()
    return df["column_name"].tolist()

SCHEMA_COLS = get_schema_cols()

def has_col(col: str) -> bool:
    return col in SCHEMA_COLS

def sql_in_list_str(values):
    safe = []
    for v in values:
        v = str(v)
        safe.append("'" + v.replace("'", "''") + "'")
    return ",".join(safe) if safe else "''"

@st.cache_data(ttl=3600)
def get_metadata():
    fecha_min = con.execute("SELECT MIN(Fecha) AS fmin FROM movimientos").fetchone()[0]
    fecha_max = con.execute("SELECT MAX(Fecha) AS fmax FROM movimientos").fetchone()[0]
    if isinstance(fecha_min, str):
        fecha_min = datetime.fromisoformat(fecha_min)
    if isinstance(fecha_max, str):
        fecha_max = datetime.fromisoformat(fecha_max)
    tiendas = con.execute("SELECT DISTINCT Tienda FROM movimientos ORDER BY Tienda").df()["Tienda"].tolist()
    proveedores = con.execute("SELECT DISTINCT Proveedor FROM movimientos ORDER BY Proveedor").df()["Proveedor"].tolist()
    return fecha_min, fecha_max, tiendas, proveedores

fecha_min, fecha_max, todas_tiendas, todas_proveedores = get_metadata()

@st.cache_data(ttl=3600)
def obtener_lista_productos():
    df = con.execute("""
        SELECT DISTINCT Codigo, Descripcion
        FROM movimientos
        WHERE Tipo_Movimiento = 'Venta'
        ORDER BY Descripcion
    """).df()
    df["Codigo"] = df["Codigo"].astype(str)
    df["display"] = df["Codigo"] + " - " + df["Descripcion"].astype(str)
    return df[["Codigo", "display"]]

df_productos_lista = obtener_lista_productos()

@st.cache_data(ttl=3600)
def get_ventas_filtradas(fecha_desde_str, fecha_hasta_str, tiendas_tuple):
    tiendas_sel = list(tiendas_tuple)
    tiendas_sql = sql_in_list_str(tiendas_sel)
    sql = f"""
        SELECT
            Fecha,
            Tienda,
            CAST(Codigo AS VARCHAR) AS Codigo,
            Descripcion,
            Tipo_Movimiento,
            Cantidad,
            Costo,
            Precio_Venta,
            Proveedor,
            Precio_Venta AS Venta_Total,
            (Cantidad * Costo) AS Costo_Total,
            (Precio_Venta - (Cantidad * Costo)) AS Margen,
            CASE
                WHEN Precio_Venta IS NULL OR Precio_Venta = 0 THEN 0
                ELSE ((Precio_Venta - (Cantidad * Costo)) / Precio_Venta) * 100
            END AS Margen_Pct
        FROM movimientos
        WHERE Tipo_Movimiento = 'Venta'
          AND Fecha >= '{fecha_desde_str}' AND Fecha <= '{fecha_hasta_str}'
          AND Tienda IN ({tiendas_sql})
    """
    df = con.execute(sql).df()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

@st.cache_data(ttl=3600)
def get_todos_filtrados(fecha_desde_str, fecha_hasta_str, tiendas_tuple):
    tiendas_sel = list(tiendas_tuple)
    tiendas_sql = sql_in_list_str(tiendas_sel)
    cols = [
        "Fecha",
        "Tienda",
        "CAST(Codigo AS VARCHAR) AS Codigo",
        "Descripcion",
        "Tipo_Movimiento",
        "Cantidad",
        "Costo",
        "Proveedor"
    ]

    if has_col("Tienda_Origen"):
        cols.append("Tienda_Origen")
    if has_col("Tienda_Destino"):
        cols.append("Tienda_Destino")

    if has_col("Numero_Documento"):
        cols.append("Numero_Documento")
    cols_sql = ",\n ".join(cols)
    sql = f"""
        SELECT
            {cols_sql},
            (Cantidad * Costo) AS Costo_Total
        FROM movimientos
        WHERE Fecha >= '{fecha_desde_str}' AND Fecha <= '{fecha_hasta_str}'
          AND Tienda IN ({tiendas_sql})
          AND Tipo_Movimiento IN ('Transferencia_Entrada','Transferencia_Salida','Recepción')
    """
    df = con.execute(sql).df()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # Info del usuario logueado
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="user-badge">👤 {usuario_actual["nombre"]}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de logout
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        logout()
    
    st.markdown("---")
    
    # Logo YUNTA
    st.markdown("""
    <div style='text-align:center; padding:1.5rem 0;'>
        <h1 style='margin:0; font-size:2.4rem; color:#60a5fa;'>YUNTA</h1>
        <p style='color:#94a3b8; margin:0.4rem 0;'>Intelligence</p>
        <p style='color:#64748b; font-size:0.85rem;'>Business Analytics</p>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Módulo",
    ["📈 Ventas 360", "🔄 Recepciones y Transferencias", "📅 Calendario Ventas", "💰 Presupuestos", "🛒 Optimizador Góndola", "💰 Simulador Pricing", "📋 Reportes Personalizados"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
if st.sidebar.button("📦 Seguimiento de Pedidos", use_container_width=True):
    st.switch_page("pages/seguimiento.py")

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros Globales")
st.sidebar.markdown("#### 📅 Período")

col1, col2 = st.sidebar.columns(2)
with col1:
    fecha_desde = st.date_input(
        "Desde",
        value=(fecha_max - timedelta(days=180)).date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        format="DD/MM/YYYY",
        key="fecha_desde"
    )
with col2:
    fecha_hasta = st.date_input(
        "Hasta",
        value=fecha_max.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
        format="DD/MM/YYYY",
        key="fecha_hasta"
    )

st.sidebar.markdown("**Rangos rápidos:**")
col1, col2, col3 = st.sidebar.columns(3)
if col1.button("30d", use_container_width=True):
    st.session_state.fecha_desde = (fecha_max - timedelta(days=30)).date()
    st.session_state.fecha_hasta = fecha_max.date()
    st.rerun()
if col2.button("3m", use_container_width=True):
    st.session_state.fecha_desde = (fecha_max - timedelta(days=90)).date()
    st.session_state.fecha_hasta = fecha_max.date()
    st.rerun()
if col3.button("6m", use_container_width=True):
    st.session_state.fecha_desde = (fecha_max - timedelta(days=180)).date()
    st.session_state.fecha_hasta = fecha_max.date()
    st.rerun()

col1, col2 = st.sidebar.columns(2)
if col1.button("1 año", use_container_width=True):
    st.session_state.fecha_desde = (fecha_max - timedelta(days=365)).date()
    st.session_state.fecha_hasta = fecha_max.date()
    st.rerun()
if col2.button("Todo", use_container_width=True):
    st.session_state.fecha_desde = fecha_min.date()
    st.session_state.fecha_hasta = fecha_max.date()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### Tiendas")

todas_tiendas_check = st.sidebar.checkbox("Seleccionar todas las tiendas", value=True, key="todas_tiendas_global")

if todas_tiendas_check:
    tiendas_sel = todas_tiendas.copy()
else:
    tiendas_sel = st.sidebar.multiselect(
        "Seleccionar tiendas específicas",
        options=todas_tiendas,
        default=['Callao'] if 'Callao' in todas_tiendas else todas_tiendas[:1],
        key="tiendas_global"
    )

st.sidebar.caption(f"Tiendas activas: {len(tiendas_sel)} / {len(todas_tiendas)}")

# ==========================================================================
# FILTROS APLICADOS
# ==========================================================================
fecha_desde_str = pd.to_datetime(fecha_desde).strftime("%Y-%m-%d")
fecha_hasta_str = pd.to_datetime(fecha_hasta).strftime("%Y-%m-%d")
tiendas_tuple = tuple(tiendas_sel)

with st.spinner("Cargando datos filtrados..."):
    df_filtrado = get_ventas_filtradas(fecha_desde_str, fecha_hasta_str, tiendas_tuple)
    df_todos_filtrado = None

    if pagina in ["🔄 Recepciones y Transferencias", "📋 Reportes Personalizados"]:
        df_todos_filtrado = get_todos_filtrados(fecha_desde_str, fecha_hasta_str, tiendas_tuple)

if df_filtrado.empty and pagina != "🔄 Recepciones y Transferencias":
    st.warning("No hay datos de ventas para el filtro seleccionado")
    st.stop()

# ============================================================================
# RECEPCIONES Y TRANSFERENCIAS (CON TABLAS EDITABLES)
# ============================================================================
if pagina == "🔄 Recepciones y Transferencias":
    st.markdown('<h1 class="main-header">🔄 Recepciones y Transferencias</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Sistema con 3 tablas editables tipo Power BI</p>', unsafe_allow_html=True)
    st.markdown("---")

    if df_todos_filtrado is None or df_todos_filtrado.empty:
        st.warning("⚠️ No hay movimientos para el filtro seleccionado")
        st.stop()

    st.markdown("### 1️⃣ Tipo de Movimiento")
    tipo_movimiento = st.selectbox(
        "Tipo de Movimiento",
        options=[
            "Transferencia_Entrada",
            "Transferencia_Salida",
            "Recepción"
        ],
        key="tipo_mov_principal"
    )

    df_base = df_todos_filtrado[
        df_todos_filtrado["Tipo_Movimiento"] == tipo_movimiento
    ].copy()

    if df_base.empty:
        st.warning(f"⚠️ No hay registros de {tipo_movimiento}")
        st.stop()

    if "Costo_Total" not in df_base.columns:
        df_base["Costo_Total"] = df_base["Cantidad"] * df_base["Costo"]

    st.markdown("---")
    st.markdown("### 2️⃣ Filtros")

    if tipo_movimiento in ["Transferencia_Entrada", "Transferencia_Salida"]:
        st.markdown("#### 🔄 Transferencias")
        col1, col2 = st.columns(2)

        tiendas_origen_disponibles = sorted(
            df_base["Tienda_Origen"].dropna().unique().tolist()
        )
        tiendas_destino_disponibles = sorted(
            df_base["Tienda_Destino"].dropna().unique().tolist()
        )

        with col1:
            st.markdown("**🏪 Tienda Origen**")
            tienda_origen_sel = st.multiselect(
                "Seleccionar tienda(s) origen",
                options=tiendas_origen_disponibles,
                default=[],
                key="filtro_tienda_origen"
            )

        with col2:
            st.markdown("**🏬 Tienda Destino**")
            tienda_destino_sel = st.multiselect(
                "Seleccionar tienda(s) destino",
                options=tiendas_destino_disponibles,
                default=[],
                key="filtro_tienda_destino"
            )

        if tienda_origen_sel:
            df_base = df_base[df_base["Tienda_Origen"].isin(tienda_origen_sel)]
        
        if tienda_destino_sel:
            df_base = df_base[df_base["Tienda_Destino"].isin(tienda_destino_sel)]

    else:
        st.markdown("#### 📦 Recepciones")

        tiendas_recepcion = st.multiselect(
            "Seleccionar Tienda(s)",
            options=sorted(df_base["Tienda"].dropna().unique().tolist()),
            default=[],
            key="filtro_tiendas_recepcion"
        )

        if tiendas_recepcion:
            df_base = df_base[df_base["Tienda"].isin(tiendas_recepcion)]

    st.markdown("---")
    st.markdown("### 3️⃣ Filtros Adicionales (Opcionales)")

    col1, col2, col3 = st.columns(3)

    with col1:
        if has_col("Numero_Documento"):
            documentos = sorted(
                df_base["Numero_Documento"].dropna().unique().tolist()
            )
            if documentos:
                doc_sel = st.multiselect(
                    "📄 Número de Documento",
                    options=documentos,
                    default=[],
                    key="filtro_documento"
                )
                if doc_sel:
                    df_base = df_base[df_base["Numero_Documento"].isin(doc_sel)]

    with col2:
        proveedores = sorted(
            df_base["Proveedor"].dropna().unique().tolist()
        )
        if proveedores:
            prov_sel = st.multiselect(
                "🏭 Proveedor",
                options=proveedores,
                default=[],
                key="filtro_proveedor"
            )
            if prov_sel:
                df_base = df_base[df_base["Proveedor"].isin(prov_sel)]

    with col3:
        buscar_prod = st.text_input(
            "🔍 Código o Descripción",
            key="filtro_producto"
        )
        if buscar_prod:
            df_base = df_base[
                df_base["Codigo"].astype(str).str.contains(buscar_prod, case=False, na=False) |
                df_base["Descripcion"].astype(str).str.contains(buscar_prod, case=False, na=False)
            ]

    if df_base.empty:
        st.warning("⚠️ No hay registros con los filtros seleccionados")
        st.stop()

    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_movimientos = len(df_base)
    total_unidades = df_base['Cantidad'].abs().sum()
    total_costo = df_base['Costo_Total'].sum()
    documentos_unicos = df_base['Numero_Documento'].nunique() if has_col("Numero_Documento") else 0
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">MOVIMIENTOS</div>
            <div class="metric-value">{format_number(total_movimientos)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">UNIDADES</div>
            <div class="metric-value">{format_number(total_unidades)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">COSTO TOTAL</div>
            <div class="metric-value">{format_currency(total_costo)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">DOCUMENTOS</div>
            <div class="metric-value">{format_number(documentos_unicos)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # TABLA 1: RESUMEN POR DOCUMENTO (EDITABLE)
    # ========================================================================
    st.markdown("### 📄 Tabla 1: Resumen por Documento (Editable)")
    
    if has_col("Numero_Documento"):
        df_tabla1 = df_base.groupby(['Fecha', 'Numero_Documento', 'Tipo_Movimiento', 'Proveedor', 'Tienda', 'Tienda_Origen', 'Tienda_Destino']).agg({
            'Costo_Total': 'sum'
        }).reset_index()
        
        df_tabla1 = df_tabla1.sort_values('Fecha', ascending=False)
        
        df_tabla1_display = df_tabla1.copy()
        df_tabla1_display['Fecha'] = pd.to_datetime(df_tabla1_display['Fecha']).dt.strftime('%d/%m/%Y')
        
        # TABLA EDITABLE
        edited_tabla1 = st.data_editor(
            df_tabla1_display.head(100), 
            use_container_width=True, 
            height=400,
            num_rows="dynamic",
            column_config={
                "Fecha": st.column_config.TextColumn("Fecha", width="medium"),
                "Numero_Documento": st.column_config.TextColumn("N° Doc", width="medium"),
                "Tipo_Movimiento": st.column_config.TextColumn("Tipo", width="medium"),
                "Proveedor": st.column_config.TextColumn("Proveedor", width="large"),
                "Tienda": st.column_config.TextColumn("Tienda", width="medium"),
                "Tienda_Origen": st.column_config.TextColumn("Origen", width="medium"),
                "Tienda_Destino": st.column_config.TextColumn("Destino", width="medium"),
                "Costo_Total": st.column_config.NumberColumn(
                    "Costo Total",
                    format="$ %.2f",
                    min_value=0
                ),
            },
            disabled=["Fecha"],
            key="tabla1_editable"
        )
        
        st.markdown(f"**Total: {format_currency(df_tabla1['Costo_Total'].sum())}**")
    else:
        st.info("📄 Columna Numero_Documento no disponible en los datos")
    
    st.markdown("---")
    
    # ========================================================================
    # TABLA 2: DETALLE POR PRODUCTO (EDITABLE)
    # ========================================================================
    st.markdown("### 📦 Tabla 2: Detalle por Producto (Editable)")
    
    df_tabla2 = df_base[['Fecha', 'Codigo', 'Descripcion', 'Proveedor', 'Cantidad', 'Costo', 'Costo_Total']].copy()
    df_tabla2 = df_tabla2.sort_values('Fecha', ascending=False).head(200)
    
    df_tabla2_display = df_tabla2.copy()
    df_tabla2_display['Fecha'] = pd.to_datetime(df_tabla2_display['Fecha']).dt.strftime('%d/%m/%Y')
    df_tabla2_display['Cantidad'] = df_tabla2_display['Cantidad'].abs()
    
    edited_tabla2 = st.data_editor(
    df_tabla2_display,
    use_container_width=True,
    height=400,
    num_rows="dynamic",
    column_config={
        "Fecha": st.column_config.TextColumn("Fecha", disabled=True, width="medium"),
        "Codigo": st.column_config.TextColumn("Código", width="medium"),
        "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
        "Proveedor": st.column_config.TextColumn("Proveedor", width="medium"),  # AGREGAR ESTA LÍNEA
        "Cantidad": st.column_config.NumberColumn(
            "Cantidad",
            help="Cantidad de unidades",
            min_value=0,
            format="%d"
        ),
        "Costo": st.column_config.NumberColumn(
            "Costo",
            help="Costo unitario",
            min_value=0,
            format="$ %.2f"
        ),
        "Costo_Total": st.column_config.NumberColumn(
            "Costo Total",
            help="Costo total calculado",
            format="$ %.2f"
        ),
    },
    key="tabla2_editable"
)
    
    st.markdown("---")
    
    # ========================================================================
    # TABLA 3: RESUMEN ORIGEN → DESTINO (EDITABLE, solo transferencias)
    # ========================================================================
    if tipo_movimiento in ["Transferencia_Entrada", "Transferencia_Salida"]:
        st.markdown("### 🔄 Tabla 3: Resumen Origen → Destino (Editable)")
        
        df_base_mes = df_base.copy()
        df_base_mes['MesNombre'] = pd.to_datetime(df_base_mes['Fecha']).dt.strftime('%B')
        
        df_tabla3 = df_base_mes.groupby(['Tienda_Origen', 'Tienda_Destino', 'MesNombre']).agg({
            'Costo_Total': 'sum'
        }).reset_index()
        
        df_tabla3 = df_tabla3.sort_values('Costo_Total', ascending=False)
        
        edited_tabla3 = st.data_editor(
            df_tabla3,
            use_container_width=True,
            height=300,
            num_rows="dynamic",
            column_config={
                "Tienda_Origen": st.column_config.SelectboxColumn(
                    "Tienda Origen",
                    options=todas_tiendas,
                    required=True
                ),
                "Tienda_Destino": st.column_config.SelectboxColumn(
                    "Tienda Destino",
                    options=todas_tiendas,
                    required=True
                ),
                "MesNombre": st.column_config.SelectboxColumn(
                    "Mes",
                    options=["January", "February", "March", "April", "May", "June", 
                            "July", "August", "September", "October", "November", "December"],
                    required=True
                ),
                "Costo_Total": st.column_config.NumberColumn(
                    "Costo Total",
                    format="$ %.2f",
                    min_value=0
                ),
            },
            key="tabla3_editable"
        )
        
        total_editado = edited_tabla3['Costo_Total'].sum()
        st.markdown(f"**Total Editado: {format_currency(total_editado)}**")
    
    st.markdown("---")
    
    # ========================================================================
    # DESCARGAS
    # ========================================================================
    st.markdown("### 📥 Descargar Reportes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if has_col("Numero_Documento"):
            excel1 = to_excel(edited_tabla1)
            st.download_button(
                label="📥 Tabla 1 (Excel)",
                data=excel1,
                file_name=f"tabla1_editada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        excel2 = to_excel(edited_tabla2)
        st.download_button(
            label="📥 Tabla 2 (Excel)",
            data=excel2,
            file_name=f"tabla2_editada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        if tipo_movimiento in ["Transferencia_Entrada", "Transferencia_Salida"]:
            excel3 = to_excel(edited_tabla3)
            st.download_button(
                label="📥 Tabla 3 (Excel)",
                data=excel3,
                file_name=f"tabla3_editada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# ============================================================================
# 📅 CALENDARIO DE VENTAS Y RECEPCIONES - Versión FINAL con export a Excel
# ============================================================================
elif pagina == "📅 Calendario Ventas":
    st.markdown('<h1 class="main-header">📅 Línea de Tiempo de Ventas y Recepciones</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tabla diaria: ventas, recepciones y días sin movimiento</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Filtros locales
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        busqueda_sku = st.text_input(
            "Buscar SKU o Descripción",
            placeholder="Ej: 7790... o 'mayonesa natura'",
            key="calendario_busqueda"
        )

    with col2:
        proveedor_cal = st.selectbox(
            "Proveedor",
            options=["Todos"] + todas_proveedores,
            key="calendario_proveedor"
        )

    with col3:
        tienda_cal = st.selectbox(
            "Tienda",
            options=["Todas"] + todas_tiendas,
            key="calendario_tienda"
        )

    # Usar fechas globales
    fecha_desde_cal = fecha_desde
    fecha_hasta_cal = fecha_hasta

    # Cargar datos
    if df_filtrado is None:
        df_filtrado = get_ventas_filtradas(fecha_desde_str, fecha_hasta_str, tiendas_tuple)

    if df_todos_filtrado is None:
        df_todos_filtrado = get_todos_filtrados(fecha_desde_str, fecha_hasta_str, tiendas_tuple)

    # Aplicar filtros locales a ambos datasets
    df_ventas_filtro = df_filtrado.copy()
    df_recep_filtro = df_todos_filtrado.copy()

    df_ventas_filtro['Fecha'] = pd.to_datetime(df_ventas_filtro['Fecha'])
    df_recep_filtro['Fecha'] = pd.to_datetime(df_recep_filtro['Fecha'])

    # Filtro fechas globales
    df_ventas_filtro = df_ventas_filtro[
        (df_ventas_filtro['Fecha'] >= pd.to_datetime(fecha_desde_cal)) &
        (df_ventas_filtro['Fecha'] <= pd.to_datetime(fecha_hasta_cal))
    ]
    df_recep_filtro = df_recep_filtro[
        (df_recep_filtro['Fecha'] >= pd.to_datetime(fecha_desde_cal)) &
        (df_recep_filtro['Fecha'] <= pd.to_datetime(fecha_hasta_cal))
    ]

    # Filtro tienda
    tiendas_filtro = tiendas_sel if len(tiendas_sel) > 0 else todas_tiendas
    if tienda_cal != "Todas":
        tiendas_filtro = [tienda_cal]
    df_ventas_filtro = df_ventas_filtro[df_ventas_filtro['Tienda'].isin(tiendas_filtro)]
    df_recep_filtro = df_recep_filtro[
        df_recep_filtro['Tienda'].isin(tiendas_filtro) |
        df_recep_filtro.get('Tienda_Destino', pd.Series()).isin(tiendas_filtro)
    ]

    # Filtro proveedor
    if proveedor_cal != "Todos":
        df_ventas_filtro = df_ventas_filtro[df_ventas_filtro['Proveedor'] == proveedor_cal]
        df_recep_filtro = df_recep_filtro[df_recep_filtro['Proveedor'] == proveedor_cal]

    # Filtro búsqueda SKU
    if busqueda_sku:
        busqueda_lower = busqueda_sku.lower()
        df_ventas_filtro = df_ventas_filtro[
            df_ventas_filtro['Descripcion'].str.lower().str.contains(busqueda_lower, na=False) |
            df_ventas_filtro['Codigo'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
        ]
        df_recep_filtro = df_recep_filtro[
            df_recep_filtro['Descripcion'].str.lower().str.contains(busqueda_lower, na=False) |
            df_recep_filtro['Codigo'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
        ]

    if df_ventas_filtro.empty and df_recep_filtro.empty:
        st.warning("No hay movimientos con los filtros actuales")
        st.stop()

    # Debug
    st.subheader("Debug")
    st.write("Ventas encontradas:", len(df_ventas_filtro))
    st.write("Recepciones encontradas:", len(df_recep_filtro))

    # Seleccionar SKU
    skus = sorted(set(df_ventas_filtro['Descripcion'].unique()) | set(df_recep_filtro['Descripcion'].unique()))
    if not skus:
        st.warning("No hay productos con movimientos después de filtros")
        st.stop()

    sku_sel = st.selectbox("Seleccionar producto", options=skus)

    # Filtrar por SKU
    df_ventas_sku = df_ventas_filtro[df_ventas_filtro['Descripcion'] == sku_sel].copy()
    df_recep_sku = df_recep_filtro[df_recep_filtro['Descripcion'] == sku_sel].copy()

    # Rango de fechas
    fechas_completas = pd.date_range(start=fecha_desde_cal, end=fecha_hasta_cal, freq='D')
    df_dias = pd.DataFrame({'Fecha': fechas_completas})

    # Eventos ventas
    df_ventas_dia = pd.DataFrame()
    if not df_ventas_sku.empty:
        df_ventas_dia = df_ventas_sku.groupby('Fecha')['Cantidad'].sum().reset_index()
        df_ventas_dia['Evento'] = 'Venta'
        df_ventas_dia['Cantidad'] = df_ventas_dia['Cantidad'].astype(int)
        df_ventas_dia['Detalle'] = df_ventas_dia['Cantidad'].apply(lambda x: f"{x} uds vendidas")

    # Eventos recepciones
    df_recep_dia = pd.DataFrame()
    if not df_recep_sku.empty:
        df_recep_dia = df_recep_sku.groupby('Fecha')['Cantidad'].sum().reset_index()
        df_recep_dia['Evento'] = 'Recepción'
        df_recep_dia['Cantidad'] = df_recep_dia['Cantidad'].astype(int)
        df_recep_dia['Detalle'] = df_recep_dia['Cantidad'].apply(lambda x: f"{x} uds recibidas")

    # Concatenar eventos
    df_eventos = pd.concat([df_ventas_dia, df_recep_dia], ignore_index=True)

    # Unir con días y rellenar sin eventos
    df_tabla = df_dias.merge(df_eventos, on='Fecha', how='left')
    df_tabla['Evento'] = df_tabla['Evento'].fillna('Sin movimiento')
    df_tabla['Cantidad'] = df_tabla['Cantidad'].fillna(0).astype(int)
    df_tabla['Detalle'] = df_tabla['Detalle'].fillna('Sin movimiento')

    # Orden: Recepción antes que Venta
    df_tabla['Orden'] = df_tabla['Evento'].map({'Recepción': 1, 'Venta': 2, 'Sin movimiento': 3})
    df_tabla = df_tabla.sort_values(['Fecha', 'Orden'])
    df_tabla = df_tabla.drop(columns=['Orden'], errors='ignore')

    # Colores
    def color_evento(row):
        if row['Evento'] == 'Venta':
            return ['background-color: #dcfce7'] * len(row)
        elif row['Evento'] == 'Recepción':
            return ['background-color: #dbeafe'] * len(row)
        else:
            return ['background-color: #fee2e2'] * len(row)

    st.markdown(f"### Tabla diaria para '{sku_sel}'")
    st.dataframe(
        df_tabla.style.apply(color_evento, axis=1),
        use_container_width=True,
        height=600
    )

    # Exportar a Excel
    from datetime import datetime
    import io

    @st.cache_data
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Calendario')
        return output.getvalue()

    excel_data = to_excel(df_tabla)

    st.download_button(
        label="📥 Exportar tabla a Excel",
        data=excel_data,
        file_name=f"calendario_{sku_sel.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="export_calendario"
    )

# ============================================================================
# PRESUPUESTOS INTELIGENTES V2 (OPTIMIZADO + MULTI-TIENDA)
# ============================================================================
elif pagina == "💰 Presupuestos":
    st.markdown('<h1 class="main-header">💰 Presupuestos Inteligentes</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Sistema de forecasting con unidades, costos y optimización de compras</p>', unsafe_allow_html=True)
    st.markdown("---")

    # ========================================================================
    # SECCIÓN 1: CONFIGURACIÓN
    # ========================================================================
    st.markdown("### 1️⃣ Configuración del Presupuesto")
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.markdown("**📅 Período a Presupuestar**")
        meses_dict = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        mes_presupuesto = st.selectbox(
            "Mes",
            options=list(meses_dict.keys()),
            format_func=lambda x: meses_dict[x],
            index=0,  # Enero por defecto
            key="mes_presupuesto"
        )
        año_presupuesto = st.selectbox(
            "Año",
            options=[2025, 2026, 2027],
            index=1,  # 2026 por defecto
            key="año_presupuesto"
        )
    
    with col2:
        st.markdown("**🏪 Tiendas (Obligatorio)**")
        
        # Opción de selección múltiple
        modo_seleccion = st.radio(
            "Modo de selección",
            options=["Una tienda", "Múltiples tiendas", "Todas las tiendas"],
            horizontal=True,
            key="modo_tiendas"
        )
        
        if modo_seleccion == "Una tienda":
            tiendas_seleccionadas = [st.selectbox(
                "Seleccionar tienda",
                options=todas_tiendas,
                key="tienda_unica_presupuesto"
            )]
        elif modo_seleccion == "Múltiples tiendas":
            tiendas_seleccionadas = st.multiselect(
                "Seleccionar tiendas",
                options=todas_tiendas,
                default=[todas_tiendas[0]] if len(todas_tiendas) > 0 else [],
                key="tiendas_multi_presupuesto"
            )
            if not tiendas_seleccionadas:
                st.warning("⚠️ Seleccioná al menos una tienda")
        else:  # Todas las tiendas
            tiendas_seleccionadas = todas_tiendas
            st.info(f"✅ Seleccionadas: {len(todas_tiendas)} tiendas")
        
        st.markdown("**📦 Filtro por Proveedor (Opcional)**")
        proveedor_presupuesto = st.selectbox(
            "Proveedor",
            options=["Todos"] + todas_proveedores,
            key="proveedor_presupuesto"
        )
    
    with col3:
        st.markdown("**🔍 Búsqueda de Producto (Opcional)**")
        busqueda_presupuesto = st.text_input(
            "Código o descripción",
            placeholder="Ej: coca, 7790...",
            key="busqueda_presupuesto"
        )
        
        st.markdown("**📊 Mostrar**")
        mostrar_opciones = st.radio(
            "Productos",
            options=["Todos", "Solo Estrellas ⭐", "A Evaluar ⚠️", "A Descartar ❌"],
            key="mostrar_presupuesto",
            horizontal=False
        )
    
    # Configuración avanzada (colapsable)
    with st.expander("⚙️ Configuración Avanzada de Cálculo"):
        st.markdown("**🎚️ Nivel de Conservadurismo:**")
        factor_conservadurismo = st.slider(
            "Ajuste del presupuesto",
            min_value=80,
            max_value=120,
            value=95,
            step=5,
            format="%d%%",
            help="90% = Conservador | 100% = Normal | 110% = Agresivo",
            key="factor_conserv"
        ) / 100
        
        if factor_conservadurismo < 0.95:
            st.info("🛡️ Modo conservador: Presupuesto reducido para minimizar riesgo")
        elif factor_conservadurismo > 1.05:
            st.warning("🚀 Modo agresivo: Presupuesto aumentado, mayor riesgo de sobrestock")
        
        st.markdown("**Ponderación para el cálculo:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            peso_promedio = st.slider("Promedio 3 meses", 0, 100, 50, 5, key="peso_prom") / 100
        with col2:
            peso_tendencia = st.slider("Tendencia", 0, 100, 30, 5, key="peso_tend") / 100
        with col3:
            peso_rotacion = st.slider("Rotación", 0, 100, 20, 5, key="peso_rot") / 100
        
        total_peso = peso_promedio + peso_tendencia + peso_rotacion
        if abs(total_peso - 1.0) > 0.01:
            st.warning(f"⚠️ La suma de ponderaciones debe ser 100%. Actual: {total_peso*100:.0f}%")
    
    st.markdown("---")
    
    # ========================================================================
    # BOTÓN GENERAR
    # ========================================================================
    if st.button("🚀 GENERAR PRESUPUESTO", use_container_width=True, type="primary"):
        
        # Validar que haya al menos una tienda
        if not tiendas_seleccionadas or len(tiendas_seleccionadas) == 0:
            st.warning("⚠️ Seleccioná al menos una tienda")
            st.stop()
        
        # Barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("Analizando datos históricos..."):
            
            # ================================================================
            # PASO 1: FILTRAR DATOS HISTÓRICOS (MULTI-TIENDA OPTIMIZADO)
            # ================================================================
            import numpy as np
            from datetime import datetime, timedelta
            
            status_text.text("📊 Filtrando datos históricos...")
            progress_bar.progress(10)
            
            # Filtrar por tiendas seleccionadas
            df_hist = df_filtrado[df_filtrado['Tienda'].isin(tiendas_seleccionadas)].copy()
            
            # Filtrar por proveedor si se seleccionó
            if proveedor_presupuesto != "Todos":
                df_hist = df_hist[df_hist['Proveedor'] == proveedor_presupuesto]
            
            # Filtrar por búsqueda si hay texto
            if busqueda_presupuesto:
                mask = (
                    df_hist['Codigo'].astype(str).str.contains(busqueda_presupuesto, case=False, na=False) |
                    df_hist['Descripcion'].astype(str).str.contains(busqueda_presupuesto, case=False, na=False)
                )
                df_hist = df_hist[mask]
            
            if df_hist.empty:
                progress_bar.empty()
                status_text.empty()
                st.warning("⚠️ No hay datos históricos para los filtros seleccionados")
                st.stop()
            
            progress_bar.progress(20)
            
            # ================================================================
            # PASO 2: PRE-CALCULAR DATOS (OPTIMIZACIÓN CLAVE)
            # ================================================================
            status_text.text("🔢 Pre-calculando métricas...")
            
            # Convertir fecha a periodo una sola vez (no en cada loop)
            df_hist['Mes'] = pd.to_datetime(df_hist['Fecha']).dt.to_period('M')
            
            # Agrupar por producto UNA SOLA VEZ
            productos_unicos = df_hist.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
                'Venta_Total': 'sum',
                'Costo_Total': 'sum',
                'Margen': 'sum',
                'Cantidad': lambda x: abs(x).sum(),
                'Fecha': 'max'
            }).reset_index()
            
            productos_unicos['Margen_Pct'] = (
                productos_unicos['Margen'] / productos_unicos['Venta_Total'] * 100
            ).fillna(0)
            
            # Calcular costo unitario y precio venta UNA SOLA VEZ
            productos_unicos['Costo_Unitario'] = (
                productos_unicos['Costo_Total'] / productos_unicos['Cantidad']
            ).replace([np.inf, -np.inf], 0).fillna(0)
            
            productos_unicos['Precio_Venta_Unitario'] = (
                productos_unicos['Venta_Total'] / productos_unicos['Cantidad']
            ).replace([np.inf, -np.inf], 0).fillna(0)
            
            # Pre-calcular ventas por producto y mes (OPTIMIZACIÓN CLAVE)
            ventas_por_prod_mes = df_hist.groupby(['Codigo', 'Mes'], observed=True).agg({
                'Venta_Total': 'sum',
                'Cantidad': lambda x: abs(x).sum()
            }).reset_index()
            
            # Pre-calcular recepciones si existen (MULTI-TIENDA OPTIMIZADO)
            recepciones_dict = {}
            if df_todos_filtrado is not None:
                status_text.text("📦 Pre-calculando recepciones...")
                recepciones_data = df_todos_filtrado[
                    (df_todos_filtrado['Tipo_Movimiento'] == 'Recepción') &
                    (df_todos_filtrado['Tienda'].isin(tiendas_seleccionadas))
                ].copy()
                
                # Agrupar recepciones por producto
                for codigo in recepciones_data['Codigo'].unique():
                    recepciones_dict[codigo] = recepciones_data[recepciones_data['Codigo'] == codigo][['Fecha', 'Cantidad']].to_dict('records')
            
            progress_bar.progress(40)
            
            # ================================================================
            # PASO 3: CALCULAR MÉTRICAS POR PRODUCTO (OPTIMIZADO)
            # ================================================================
            status_text.text("💡 Calculando presupuesto por producto...")
            
            resultados = []
            total_productos = len(productos_unicos)
            
            for idx, prod in productos_unicos.iterrows():
                # Actualizar progreso cada 10 productos
                if idx % 10 == 0:
                    progreso_actual = 40 + int((idx / total_productos) * 50)
                    progress_bar.progress(progreso_actual)
                    status_text.text(f"💡 Procesando producto {idx + 1} de {total_productos}...")
                
                codigo = prod['Codigo']
                
                # Obtener ventas mensuales pre-calculadas (RÁPIDO)
                ventas_por_mes = ventas_por_prod_mes[ventas_por_prod_mes['Codigo'] == codigo].copy()
                
                if len(ventas_por_mes) == 0:
                    continue
                
                # Ordenar por mes
                ventas_por_mes = ventas_por_mes.sort_values('Mes')
                
                # 1. PROMEDIO ÚLTIMOS 3 MESES (UNIDADES)
                ultimos_3_meses = ventas_por_mes.tail(3)
                promedio_3m_unidades = ultimos_3_meses['Cantidad'].mean() if len(ultimos_3_meses) > 0 else 0
                
                # 2. TENDENCIA (regresión lineal)
                if len(ventas_por_mes) >= 3:
                    x = np.arange(len(ventas_por_mes))
                    y = ventas_por_mes['Cantidad'].values
                    try:
                        coef = np.polyfit(x, y, 1)
                        tendencia_slope = coef[0]
                        tendencia_unidades = coef[1] + coef[0] * len(ventas_por_mes)
                        tendencia_unidades = max(0, tendencia_unidades)
                        
                        # Clasificar tendencia
                        if tendencia_slope > 0.05 * promedio_3m_unidades:
                            tendencia_icono = "↗"
                            factor_tendencia = 1.05
                        elif tendencia_slope < -0.05 * promedio_3m_unidades:
                            tendencia_icono = "↘"
                            factor_tendencia = 0.95
                        else:
                            tendencia_icono = "→"
                            factor_tendencia = 1.0
                    except:
                        tendencia_unidades = promedio_3m_unidades
                        tendencia_icono = "→"
                        factor_tendencia = 1.0
                else:
                    tendencia_unidades = promedio_3m_unidades
                    tendencia_icono = "→"
                    factor_tendencia = 1.0
                
                # 3. COEFICIENTE DE VARIACIÓN (estabilidad)
                cv = ventas_por_mes['Cantidad'].std() / ventas_por_mes['Cantidad'].mean() if ventas_por_mes['Cantidad'].mean() > 0 else 0
                
                # 4. ROTACIÓN POST-RECEPCIÓN (OPTIMIZADO)
                rotacion_promedio = 0.5  # Default
                
                if codigo in recepciones_dict:
                    recepciones_prod = recepciones_dict[codigo]
                    rotaciones = []
                    
                    # Crear un lookup rápido de ventas por fecha
                    ventas_producto = df_hist[df_hist['Codigo'] == codigo][['Fecha', 'Cantidad']].copy()
                    
                    for recep in recepciones_prod:
                        fecha_recep = recep['Fecha']
                        fecha_7d = fecha_recep + timedelta(days=7)
                        
                        # Filtrar ventas 7 días (OPTIMIZADO)
                        ventas_7d = ventas_producto[
                            (ventas_producto['Fecha'] >= fecha_recep) &
                            (ventas_producto['Fecha'] <= fecha_7d)
                        ]['Cantidad'].abs().sum()
                        
                        cantidad_recep = abs(recep['Cantidad'])
                        if cantidad_recep > 0:
                            rotaciones.append(ventas_7d / cantidad_recep)
                    
                    if len(rotaciones) > 0:
                        rotacion_promedio = np.mean(rotaciones)
                
                # 5. ÚLTIMA VENTA
                ultima_venta = prod['Fecha']
                dias_sin_venta = (datetime.now() - ultima_venta).days if pd.notna(ultima_venta) else 999
                
                # ============================================================
                # CÁLCULO DE UNIDADES A COMPRAR
                # ============================================================
                
                # Componentes
                comp_promedio = promedio_3m_unidades
                comp_tendencia = tendencia_unidades
                comp_rotacion = promedio_3m_unidades * (rotacion_promedio / 0.65)
                
                # Unidades sugeridas (ponderado)
                unidades_sugeridas = (
                    peso_promedio * comp_promedio +
                    peso_tendencia * comp_tendencia +
                    peso_rotacion * comp_rotacion
                )
                
                # Ajuste por tendencia
                unidades_sugeridas *= factor_tendencia
                
                # Ajuste por estabilidad
                if cv > 0.7:
                    unidades_sugeridas *= 0.9
                
                # Ajuste por rotación
                if rotacion_promedio > 0.8:
                    unidades_sugeridas *= 1.1
                elif rotacion_promedio < 0.3:
                    unidades_sugeridas *= 0.8
                
                # Ajuste por conservadurismo
                unidades_finales = unidades_sugeridas * factor_conservadurismo
                unidades_finales = max(0, round(unidades_finales))
                
                # ============================================================
                # CÁLCULO DE PESOS
                # ============================================================
                
                costo_unitario = prod['Costo_Unitario']
                precio_venta_unitario = prod['Precio_Venta_Unitario']
                
                # A COMPRAR
                pesos_a_comprar = unidades_finales * costo_unitario
                
                # A VENDER
                pesos_a_vender = unidades_finales * precio_venta_unitario
                
                # MARGEN
                margen_unitario = precio_venta_unitario - costo_unitario
                margen_total = pesos_a_vender - pesos_a_comprar
                margen_pct_proyectado = (margen_total / pesos_a_vender * 100) if pesos_a_vender > 0 else 0
                
                # ============================================================
                # CÁLCULO DEL SCORE
                # ============================================================
                
                venta_total = prod['Venta_Total']
                margen_pct = prod['Margen_Pct']
                
                max_venta = productos_unicos['Venta_Total'].max()
                score_venta = min(venta_total / max_venta, 1) if max_venta > 0 else 0
                score_margen = min(margen_pct / 40, 1) if margen_pct > 0 else 0
                score_rotacion = min(rotacion_promedio, 1)
                score_estabilidad = max(0, 1 - min(cv, 1))
                
                score = (
                    40 * score_venta +
                    30 * score_margen +
                    20 * score_rotacion +
                    10 * score_estabilidad
                )
                
                # Clasificación
                if score > 75:
                    categoria = "⭐"
                    accion = "Aumentar +10%"
                elif score > 50:
                    categoria = "✅"
                    accion = "Mantener"
                elif score > 25:
                    categoria = "⚠️"
                    accion = "Revisar"
                else:
                    categoria = "❌"
                    if dias_sin_venta > 60:
                        accion = "Descontinuar"
                    else:
                        accion = "Evaluar descarte"
                
                # Guardar resultado
                resultados.append({
                    'Categoria': categoria,
                    'Codigo': codigo,
                    'Descripcion': prod['Descripcion'],
                    'Proveedor': prod['Proveedor'],
                    'Prom_3M_Unidades': promedio_3m_unidades,
                    'Tendencia': tendencia_icono,
                    'Rotacion': rotacion_promedio,
                    'Margen_Pct': margen_pct,
                    'Costo_Unitario': costo_unitario,
                    'Precio_Venta_Unitario': precio_venta_unitario,
                    'Score': score,
                    'Unidades_A_Comprar': unidades_finales,
                    'Pesos_A_Comprar': pesos_a_comprar,
                    'Unidades_A_Vender': unidades_finales,
                    'Pesos_A_Vender': pesos_a_vender,
                    'Margen_Unitario': margen_unitario,
                    'Margen_Total': margen_total,
                    'Margen_Pct_Proyectado': margen_pct_proyectado,
                    'Accion': accion,
                    'Dias_Sin_Venta': dias_sin_venta,
                    'CV': cv
                })
            
            progress_bar.progress(90)
            status_text.text("✅ Finalizando...")
            
            # Crear DataFrame de resultados
            df_presupuesto = pd.DataFrame(resultados)
            
            if df_presupuesto.empty:
                progress_bar.empty()
                status_text.empty()
                st.warning("⚠️ No se pudo generar presupuesto con los datos disponibles")
                st.stop()
            
            # Ordenar por score descendente
            df_presupuesto = df_presupuesto.sort_values('Score', ascending=False)
            
            progress_bar.progress(100)
            progress_bar.empty()
            status_text.empty()
            
            # ================================================================
            # FILTRAR POR CATEGORÍA SI SE SELECCIONÓ
            # ================================================================
            if mostrar_opciones == "Solo Estrellas ⭐":
                df_presupuesto = df_presupuesto[df_presupuesto['Categoria'] == "⭐"]
            elif mostrar_opciones == "A Evaluar ⚠️":
                df_presupuesto = df_presupuesto[df_presupuesto['Categoria'] == "⚠️"]
            elif mostrar_opciones == "A Descartar ❌":
                df_presupuesto = df_presupuesto[df_presupuesto['Categoria'] == "❌"]
            
            # ================================================================
            # SECCIÓN 2: MÉTRICAS GENERALES (5 CARDS)
            # ================================================================
            st.markdown("---")
            
            # Título dinámico según cantidad de tiendas
            if len(tiendas_seleccionadas) == 1:
                titulo_tiendas = tiendas_seleccionadas[0]
            elif len(tiendas_seleccionadas) <= 3:
                titulo_tiendas = ", ".join(tiendas_seleccionadas)
            else:
                titulo_tiendas = f"{len(tiendas_seleccionadas)} tiendas"
            
            st.markdown(f"### 📊 Presupuesto {meses_dict[mes_presupuesto]} {año_presupuesto} - {titulo_tiendas}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            unidades_totales = df_presupuesto['Unidades_A_Comprar'].sum()
            compras_totales = df_presupuesto['Pesos_A_Comprar'].sum()
            ventas_totales = df_presupuesto['Pesos_A_Vender'].sum()
            margen_total = df_presupuesto['Margen_Total'].sum()
            margen_pct_total = (margen_total / ventas_totales * 100) if ventas_totales > 0 else 0
            productos_activos = len(df_presupuesto[df_presupuesto['Unidades_A_Comprar'] > 0])
            
            with col1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">📦 UNIDADES</div>
                    <div class="metric-value">{format_number(unidades_totales)}</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">A comprar</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">💰 COMPRAS</div>
                    <div class="metric-value" style="font-size:1.8rem;">{format_currency(compras_totales)}</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">Inversión necesaria</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">📊 VENTAS</div>
                    <div class="metric-value" style="font-size:1.8rem;">{format_currency(ventas_totales)}</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">Facturación esperada</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">💵 MARGEN</div>
                    <div class="metric-value" style="font-size:1.8rem;">{format_currency(margen_total)}</div>
                    <div style="font-size:0.8rem; color:#94a3b8;">{format_percent(margen_pct_total)}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col5:
                estrellas = len(df_presupuesto[df_presupuesto['Categoria'] == "⭐"])
                a_descartar = len(df_presupuesto[df_presupuesto['Categoria'] == "❌"])
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-label">📋 PRODUCTOS</div>
                    <div class="metric-value">{productos_activos}</div>
                    <div style="font-size:0.8rem; color:#10b981;">⭐ {estrellas} estrellas</div>
                    <div style="font-size:0.8rem; color:#ef4444;">❌ {a_descartar} a descartar</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # ================================================================
            # ALERTAS
            # ================================================================
            st.markdown("---")
            
            # Productos con baja rotación
            baja_rotacion = df_presupuesto[df_presupuesto['Rotacion'] < 0.3]
            capital_inmovilizado = baja_rotacion['Pesos_A_Comprar'].sum()
            
            # Productos sin venta reciente
            sin_venta_60d = df_presupuesto[df_presupuesto['Dias_Sin_Venta'] > 60]
            
            if len(baja_rotacion) > 0 or len(sin_venta_60d) > 0:
                with st.expander("⚠️ ALERTAS DE RIESGO", expanded=True):
                    if len(baja_rotacion) > 0:
                        st.warning(f"🐌 **{len(baja_rotacion)} productos con baja rotación** (<30%)  \nCapital en riesgo: {format_currency(capital_inmovilizado)}")
                    
                    if len(sin_venta_60d) > 0:
                        st.error(f"🚫 **{len(sin_venta_60d)} productos sin venta en 60+ días**  \nConsiderar descarte para liberar capital")
            
            # ================================================================
            # SECCIÓN 3: TABLA EDITABLE
            # ================================================================
            st.markdown("---")
            st.markdown("### 📋 Presupuesto Detallado por Producto (Editable)")
            
            # Preparar tabla para display
            df_display = df_presupuesto.copy()
            
            # Convertir rotación a % para display
            df_display['Rotacion'] = df_display['Rotacion'] * 100
            
            # Crear tabla editable
            edited_presupuesto = st.data_editor(
                df_display,
                use_container_width=True,
                height=500,
                num_rows="dynamic",
                column_config={
                    "Categoria": st.column_config.TextColumn("Cat", width="small"),
                    "Codigo": st.column_config.TextColumn("Código", width="small"),
                    "Descripcion": st.column_config.TextColumn("Descripción", width="large"),
                    "Proveedor": st.column_config.TextColumn("Proveedor", width="medium"),
                    "Prom_3M_Unidades": st.column_config.NumberColumn(
                        "Prom 3M (u)",
                        format="%.0f u",
                        width="small"
                    ),
                    "Tendencia": st.column_config.TextColumn("Tend", width="small"),
                    "Rotacion": st.column_config.NumberColumn(
                        "Rot %",
                        format="%.0f%%",
                        width="small"
                    ),
                    "Margen_Pct": st.column_config.NumberColumn(
                        "Mg %",
                        format="%.1f%%",
                        width="small"
                    ),
                    "Costo_Unitario": st.column_config.NumberColumn(
                        "Costo Unit",
                        format="$ %.2f",
                        width="small"
                    ),
                    "Precio_Venta_Unitario": st.column_config.NumberColumn(
                        "PV Unit",
                        format="$ %.2f",
                        width="small"
                    ),
                    "Score": st.column_config.NumberColumn(
                        "Score",
                        format="%.0f",
                        width="small"
                    ),
                    "Unidades_A_Comprar": st.column_config.NumberColumn(
                        "🛒 Unid Comprar",
                        format="%.0f u",
                        width="medium"
                    ),
                    "Pesos_A_Comprar": st.column_config.NumberColumn(
                        "💰 $ Comprar",
                        format="$ %.0f",
                        width="medium"
                    ),
                    "Unidades_A_Vender": st.column_config.NumberColumn(
                        "📊 Unid Vender",
                        format="%.0f u",
                        width="medium",
                        disabled=True
                    ),
                    "Pesos_A_Vender": st.column_config.NumberColumn(
                        "💵 $ Vender",
                        format="$ %.0f",
                        width="medium",
                        disabled=True
                    ),
                    "Margen_Total": st.column_config.NumberColumn(
                        "Margen $",
                        format="$ %.0f",
                        width="medium",
                        disabled=True
                    ),
                    "Accion": st.column_config.TextColumn("Acción", width="medium"),
                },
                disabled=["Categoria", "Codigo", "Descripcion", "Proveedor", "Prom_3M_Unidades", 
                         "Tendencia", "Rotacion", "Margen_Pct", "Costo_Unitario", 
                         "Precio_Venta_Unitario", "Score", "Pesos_A_Comprar", 
                         "Unidades_A_Vender", "Pesos_A_Vender", "Margen_Total"],
                hide_index=True,
                key="tabla_presupuesto_editable"
            )
            
            # Recalcular totales si se editó
            edited_presupuesto['Pesos_A_Comprar'] = edited_presupuesto['Unidades_A_Comprar'] * edited_presupuesto['Costo_Unitario']
            edited_presupuesto['Pesos_A_Vender'] = edited_presupuesto['Unidades_A_Comprar'] * edited_presupuesto['Precio_Venta_Unitario']
            edited_presupuesto['Margen_Total'] = edited_presupuesto['Pesos_A_Vender'] - edited_presupuesto['Pesos_A_Comprar']
            
            # Totales ajustados
            unidades_ajustadas = edited_presupuesto['Unidades_A_Comprar'].sum()
            compras_ajustadas = edited_presupuesto['Pesos_A_Comprar'].sum()
            ventas_ajustadas = edited_presupuesto['Pesos_A_Vender'].sum()
            margen_ajustado = edited_presupuesto['Margen_Total'].sum()
            
            st.markdown(f"""
            **📦 Unidades:** {format_number(unidades_totales)} → {format_number(unidades_ajustadas)}  
            **💰 Inversión:** {format_currency(compras_totales)} → {format_currency(compras_ajustadas)}  
            **📊 Ventas:** {format_currency(ventas_totales)} → {format_currency(ventas_ajustadas)}  
            **💵 Margen:** {format_currency(margen_total)} → {format_currency(margen_ajustado)}
            """)

            # ================================================================
            # SECCIÓN 3.1: CUMPLIMIENTO DE PRESUPUESTO (MES)
            # ================================================================
            st.markdown("---")
            st.markdown("### ✅ Cumplimiento del Presupuesto")

            inicio_mes = datetime(año_presupuesto, mes_presupuesto, 1)
            fin_mes = (pd.Timestamp(inicio_mes) + pd.offsets.MonthEnd(0)).to_pydatetime()
            inicio_str = inicio_mes.strftime("%Y-%m-%d")
            fin_str = fin_mes.strftime("%Y-%m-%d")

            df_actual_mes = get_ventas_filtradas(inicio_str, fin_str, tuple(tiendas_seleccionadas))

            if proveedor_presupuesto != "Todos":
                df_actual_mes = df_actual_mes[df_actual_mes['Proveedor'] == proveedor_presupuesto]
            if busqueda_presupuesto:
                mask = (
                    df_actual_mes['Codigo'].astype(str).str.contains(busqueda_presupuesto, case=False, na=False) |
                    df_actual_mes['Descripcion'].astype(str).str.contains(busqueda_presupuesto, case=False, na=False)
                )
                df_actual_mes = df_actual_mes[mask]

            if df_actual_mes.empty:
                st.warning("⚠️ No hay ventas reales para el mes seleccionado con estos filtros")
            else:
                df_actual_prod = df_actual_mes.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
                    'Venta_Total': 'sum',
                    'Cantidad': lambda x: abs(x).sum()
                }).reset_index()
                df_actual_prod.rename(columns={
                    'Venta_Total': 'Ventas_Actual',
                    'Cantidad': 'Unidades_Actual'
                }, inplace=True)

                df_comp = edited_presupuesto.merge(
                    df_actual_prod,
                    on=['Codigo', 'Descripcion', 'Proveedor'],
                    how='left'
                )

                df_comp['Ventas_Actual'] = df_comp['Ventas_Actual'].fillna(0)
                df_comp['Unidades_Actual'] = df_comp['Unidades_Actual'].fillna(0)
                df_comp['Cumplimiento_Ventas_Pct'] = (
                    df_comp['Ventas_Actual'] / df_comp['Pesos_A_Vender'].replace(0, pd.NA) * 100
                ).fillna(0)
                df_comp['Cumplimiento_Unidades_Pct'] = (
                    df_comp['Unidades_Actual'] / df_comp['Unidades_A_Vender'].replace(0, pd.NA) * 100
                ).fillna(0)

                ventas_presupuesto = df_comp['Pesos_A_Vender'].sum()
                ventas_reales = df_comp['Ventas_Actual'].sum()
                cumplimiento_global = (ventas_reales / ventas_presupuesto * 100) if ventas_presupuesto > 0 else 0
                delta_ventas = ventas_reales - ventas_presupuesto

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Presupuesto $", format_currency(ventas_presupuesto))
                with col2:
                    st.metric("Ventas reales $", format_currency(ventas_reales))
                with col3:
                    st.metric("Cumplimiento %", f"{cumplimiento_global:.1f}%")
                with col4:
                    st.metric("Brecha $", format_currency(delta_ventas))

                st.markdown("#### Desvíos principales (Top)")
                df_comp['Brecha_$'] = df_comp['Ventas_Actual'] - df_comp['Pesos_A_Vender']
                df_desv = df_comp.sort_values('Brecha_$')

                st.dataframe(
                    df_desv[[
                        'Codigo', 'Descripcion', 'Proveedor',
                        'Pesos_A_Vender', 'Ventas_Actual', 'Brecha_$',
                        'Cumplimiento_Ventas_Pct'
                    ]].head(50),
                    use_container_width=True,
                    height=350,
                    column_config={
                        'Pesos_A_Vender': st.column_config.NumberColumn(format="$%.0f"),
                        'Ventas_Actual': st.column_config.NumberColumn(format="$%.0f"),
                        'Brecha_$': st.column_config.NumberColumn(format="$%.0f"),
                        'Cumplimiento_Ventas_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    }
                )

                df_top_chart = df_comp.sort_values('Pesos_A_Vender', ascending=False).head(20).copy()
                df_top_chart['Producto'] = df_top_chart['Codigo'].astype(str) + " - " + df_top_chart['Descripcion'].astype(str).str[:30]

                fig_comp = px.bar(
                    df_top_chart,
                    x='Producto',
                    y=['Pesos_A_Vender', 'Ventas_Actual'],
                    title='Presupuesto vs Ventas reales (Top 20)',
                    labels={'value': '$', 'variable': 'Tipo'}
                )
                fig_comp.update_layout(height=420, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_comp, use_container_width=True)

                excel_comp = to_excel(df_comp)
                st.download_button(
                    label="📥 Exportar cumplimiento",
                    data=excel_comp,
                    file_name=f"cumplimiento_presupuesto_{meses_dict[mes_presupuesto]}_{año_presupuesto}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                # ================================================================
                # DIAGNÓSTICO DE CAUSAS (Faltante vs Sobre-presupuesto vs Precio)
                # ================================================================
                st.markdown("---")
                st.markdown("### 🧠 Diagnóstico de causas")

                df_actual_mes['Fecha'] = pd.to_datetime(df_actual_mes['Fecha'])
                dias_con_venta = df_actual_mes.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True)['Fecha'].nunique().reset_index()
                dias_con_venta.rename(columns={'Fecha': 'Dias_Con_Venta'}, inplace=True)

                dias_mes = (fin_mes.date() - inicio_mes.date()).days + 1

                # Precio unitario actual (mes)
                df_precio_actual = df_actual_mes.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
                    'Venta_Total': 'sum',
                    'Cantidad': lambda x: abs(x).sum()
                }).reset_index()
                df_precio_actual['Precio_Unit_Actual'] = (
                    df_precio_actual['Venta_Total'] / df_precio_actual['Cantidad'].replace(0, pd.NA)
                ).fillna(0)

                # Precio unitario histórico (últimos 3 meses previos)
                fecha_inicio_hist = inicio_mes - timedelta(days=90)
                df_hist_3m = df_hist[(df_hist['Fecha'] >= fecha_inicio_hist) & (df_hist['Fecha'] < inicio_mes)].copy()
                df_precio_hist = df_hist_3m.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
                    'Venta_Total': 'sum',
                    'Cantidad': lambda x: abs(x).sum()
                }).reset_index()
                df_precio_hist['Precio_Unit_Hist'] = (
                    df_precio_hist['Venta_Total'] / df_precio_hist['Cantidad'].replace(0, pd.NA)
                ).fillna(0)

                df_diag = df_comp.merge(dias_con_venta, on=['Codigo', 'Descripcion', 'Proveedor'], how='left')
                df_diag = df_diag.merge(df_precio_actual[['Codigo', 'Descripcion', 'Proveedor', 'Precio_Unit_Actual']],
                                        on=['Codigo', 'Descripcion', 'Proveedor'], how='left')
                df_diag = df_diag.merge(df_precio_hist[['Codigo', 'Descripcion', 'Proveedor', 'Precio_Unit_Hist']],
                                        on=['Codigo', 'Descripcion', 'Proveedor'], how='left')

                df_diag['Dias_Con_Venta'] = df_diag['Dias_Con_Venta'].fillna(0)
                df_diag['Disponibilidad_Pct'] = (df_diag['Dias_Con_Venta'] / dias_mes * 100).fillna(0)
                df_diag['Precio_Unit_Actual'] = df_diag['Precio_Unit_Actual'].fillna(0)
                df_diag['Precio_Unit_Hist'] = df_diag['Precio_Unit_Hist'].fillna(0)
                df_diag['Desvio_Precio_Pct'] = (
                    (df_diag['Precio_Unit_Actual'] - df_diag['Precio_Unit_Hist']) /
                    df_diag['Precio_Unit_Hist'].replace(0, pd.NA) * 100
                ).fillna(0)

                def clasificar_causa(row):
                    if row['Cumplimiento_Ventas_Pct'] < 80:
                        if row['Disponibilidad_Pct'] < 60:
                            return "Faltante/Quiebre"
                        if row['Desvio_Precio_Pct'] > 15:
                            return "Precio alto"
                        return "Sobre-presupuesto"
                    if row['Cumplimiento_Ventas_Pct'] > 110:
                        return "Sub-presupuesto"
                    return "OK"

                def recomendacion(row):
                    if row['Causa'] == "Faltante/Quiebre":
                        return "Aumentar compra o mejorar reposición"
                    if row['Causa'] == "Precio alto":
                        return "Revisar precio/promoción"
                    if row['Causa'] == "Sobre-presupuesto":
                        return "Reducir presupuesto"
                    if row['Causa'] == "Sub-presupuesto":
                        return "Aumentar presupuesto"
                    return "Mantener"

                df_diag['Causa'] = df_diag.apply(clasificar_causa, axis=1)
                df_diag['Recomendacion'] = df_diag.apply(recomendacion, axis=1)

                # KPIs de diagnóstico
                total_diag = len(df_diag)
                faltantes = len(df_diag[df_diag['Causa'] == "Faltante/Quiebre"])
                sobre = len(df_diag[df_diag['Causa'] == "Sobre-presupuesto"])
                precio = len(df_diag[df_diag['Causa'] == "Precio alto"])
                sub = len(df_diag[df_diag['Causa'] == "Sub-presupuesto"])

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Faltante/Quiebre", f"{faltantes} ({(faltantes/total_diag*100):.1f}%)" if total_diag else "0")
                with col2:
                    st.metric("Sobre-presupuesto", f"{sobre} ({(sobre/total_diag*100):.1f}%)" if total_diag else "0")
                with col3:
                    st.metric("Precio alto", f"{precio} ({(precio/total_diag*100):.1f}%)" if total_diag else "0")
                with col4:
                    st.metric("Sub-presupuesto", f"{sub} ({(sub/total_diag*100):.1f}%)" if total_diag else "0")

                st.markdown("#### Top brechas con causa")
                df_diag['Brecha_$'] = df_diag['Ventas_Actual'] - df_diag['Pesos_A_Vender']
                df_diag_sorted = df_diag.sort_values('Brecha_$')

                st.dataframe(
                    df_diag_sorted[[
                        'Codigo', 'Descripcion', 'Proveedor',
                        'Pesos_A_Vender', 'Ventas_Actual', 'Brecha_$',
                        'Cumplimiento_Ventas_Pct', 'Disponibilidad_Pct', 'Desvio_Precio_Pct',
                        'Causa', 'Recomendacion'
                    ]].head(50),
                    use_container_width=True,
                    height=400,
                    column_config={
                        'Pesos_A_Vender': st.column_config.NumberColumn(format="$%.0f"),
                        'Ventas_Actual': st.column_config.NumberColumn(format="$%.0f"),
                        'Brecha_$': st.column_config.NumberColumn(format="$%.0f"),
                        'Cumplimiento_Ventas_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                        'Disponibilidad_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                        'Desvio_Precio_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    }
                )

                excel_diag = to_excel(df_diag)
                st.download_button(
                    label="📥 Exportar diagnóstico",
                    data=excel_diag,
                    file_name=f"diagnostico_presupuesto_{meses_dict[mes_presupuesto]}_{año_presupuesto}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
    # ================================================================
    # SECCIÓN 4: ANÁLISIS VISUAL
    # ================================================================
    st.markdown("---")
    st.markdown("### 📊 Análisis Visual")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Por Categoría",
        "🎯 Matriz Decisión",
        "⭐ Top 10",
        "🏭 Por Proveedor"
    ])

    # ------------------------------------------------
    # TAB 1 - POR CATEGORÍA
    # ------------------------------------------------
    with tab1:
        st.markdown("#### Productos por Categoría")

        categoria_counts = df_presupuesto['Categoria'].value_counts()

        fig_cat = px.bar(
            x=categoria_counts.index,
            y=categoria_counts.values,
            labels={
                'x': 'Categoría',
                'y': 'Cantidad de Productos'
            },
            color=categoria_counts.index,
            color_discrete_map={
                "⭐": "#10b981",
                "✅": "#3b82f6",
                "⚠️": "#f59e0b",
                "❌": "#ef4444"
            }
        )

    fig_cat.update_layout(
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )

    st.plotly_chart(fig_cat, use_container_width=True)

    # ------------------------------------------------
    # TAB 2 - MATRIZ DE DECISIÓN
    # ------------------------------------------------
    with tab2:
        st.markdown("#### Matriz de Decisión: Margen vs Rotación")

        # Copia de seguridad
        df_scatter = df_presupuesto.copy()

        # Tamaño del punto basado en pesos (valor absoluto)
        df_scatter['Size_Positive'] = (
            df_scatter['Pesos_A_Vender']
            .fillna(0)
            .abs()
        )

        max_size = df_scatter['Size_Positive'].max()

        if max_size > 0:
            df_scatter['Size_Scaled'] = (
                 df_scatter['Size_Positive'] / max_size
            ) * 40 + 5
        else:
            df_scatter['Size_Scaled'] = 10

        fig_scatter = px.scatter(
            df_scatter,
            x='Rotacion',
            y='Margen_Pct',
            color='Categoria',
            size='Size_Scaled',
            hover_data=[
                'Codigo',
                'Descripcion',
                'Score',
                'Unidades_A_Comprar',
                'Pesos_A_Vender'
            ],
            color_discrete_map={
                "⭐": "#10b981",
                "✅": "#3b82f6",
                "⚠️": "#f59e0b",
                "❌": "#ef4444"
            },
            labels={
                'Rotacion': 'Rotación Post-Recepción (%)',
                'Margen_Pct': 'Margen %'
            }
        )

        fig_scatter.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        if (df_presupuesto['Pesos_A_Vender'] < 0).any():
            st.warning(
                "⚠️ Algunos valores de **Pesos_A_Vender** son negativos "
                "(pérdida proyectada). El tamaño del punto usa valor absoluto."
            )

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.info(
            "💡 **Zona superior derecha** = Alta rotación + Alto margen "
            "(⭐ Productos estrella)"
        )
 
    # ================================================================
    # SECCIÓN 5: EXPORTACIÓN
    # ================================================================
    st.markdown("---")
    st.markdown("### 📥 Exportar Presupuesto")

    col1, col2, col3 = st.columns(3)

    if len(tiendas_seleccionadas) == 1:
        nombre_tiendas = tiendas_seleccionadas[0]
    else:
        nombre_tiendas = f"{len(tiendas_seleccionadas)}_tiendas"

    with col1:
        df_export = edited_presupuesto[[
            'Categoria', 'Codigo', 'Descripcion', 'Proveedor',
            'Unidades_A_Comprar', 'Pesos_A_Comprar',
            'Pesos_A_Vender', 'Margen_Total', 'Score', 'Accion'
        ]].copy()

        excel_presupuesto = to_excel(df_export)
        st.download_button(
            label="📥 Excel Completo",
            data=excel_presupuesto,
            file_name=f"presupuesto_{nombre_tiendas}_{meses_dict[mes_presupuesto]}_{año_presupuesto}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col2:
        df_orden_compra = edited_presupuesto[
            edited_presupuesto['Unidades_A_Comprar'] > 0
        ][['Proveedor', 'Codigo', 'Descripcion', 'Unidades_A_Comprar', 'Pesos_A_Comprar']]

        df_orden_compra = df_orden_compra.sort_values(
            ['Proveedor', 'Pesos_A_Comprar'], ascending=[True, False]
        )

        excel_orden = to_excel(df_orden_compra)
        st.download_button(
            label="🛒 Orden de Compra",
            data=excel_orden,
            file_name=f"orden_compra_{nombre_tiendas}_{meses_dict[mes_presupuesto]}_{año_presupuesto}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col3:
        df_csv = edited_presupuesto[
            ['Proveedor', 'Codigo', 'Descripcion', 'Unidades_A_Comprar', 'Pesos_A_Comprar']
        ].copy()

        csv_data = df_csv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 CSV Simple",
            data=csv_data,
            file_name=f"presupuesto_simple_{nombre_tiendas}_{meses_dict[mes_presupuesto]}_{año_presupuesto}.csv",
            mime="text/csv",
            use_container_width=True
        )
    # ------------------------------------------------
    # TAB 3 - TOP 10
    # ------------------------------------------------
    with tab3:
        st.markdown("#### ⭐ Top 10 Productos por Score")

        top10 = (
            df_presupuesto
            .sort_values('Score', ascending=False)
            .head(10)
        )

        st.dataframe(
            top10[
                [
                    'Codigo',
                    'Descripcion',
                    'Categoria',
                    'Score',
                    'Margen_Pct',
                    'Rotacion',
                    'Pesos_A_Vender'
                ]
            ],
            use_container_width=True
        )

    # ------------------------------------------------
    # TAB 4 - POR PROVEEDOR
    # ------------------------------------------------
    with tab4:
        st.markdown("#### 🏭 Análisis por Proveedor")

        proveedor_resumen = (
            df_presupuesto
            .groupby('Proveedor', as_index=False)
            .agg(
                Productos=('Codigo', 'count'),
                Venta_Estimada=('Pesos_A_Vender', 'sum'),
                Margen_Promedio=('Margen_Pct', 'mean')
            )
            .sort_values('Venta_Estimada', ascending=False)
        )

        fig_prov = px.bar(
            proveedor_resumen,
            x='Proveedor',
            y='Venta_Estimada',
            hover_data=['Productos', 'Margen_Promedio'],
            labels={
                'Venta_Estimada': 'Venta Estimada ($)'
            }
        )

        fig_prov.update_layout(
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_prov, use_container_width=True)


# ============================================================================
# 🛒 OPTIMIZADOR DE GÓNDOLA V2 - Con recomendaciones de espacio
# ============================================================================
elif pagina == "🛒 Optimizador Góndola":
    st.markdown('<h1 class="main-header">🛒 Optimizador de Góndola</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Optimiza el espacio en góndola: ampliar lo que vende, sacar lo que no rota</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 1: FILTROS
    # ========================================================================
    st.markdown("### 🔍 Filtros")

    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        busqueda_gondola = st.text_input(
            "Buscar por nombre o código (opcional)",
            placeholder="Ej: yerba, coca, 7790...",
            key="busqueda_gondola",
            help="Dejar vacío = todos los productos del proveedor"
        )

    with col2:
        proveedor_gondola = st.selectbox(
            "Proveedor",
            options=["Selecciona un proveedor"] + ["Todos"] + todas_proveedores,
            index=0,
            key="proveedor_gondola"
        )

    with col3:
        tienda_gondola = st.selectbox(
            "Tienda",
            options=["Todas"] + todas_tiendas,
            key="tienda_gondola"
        )

    # Validaciones
    if proveedor_gondola == "Selecciona un proveedor":
        st.info("💡 Elegí un proveedor para comenzar")
        st.stop()

    if not busqueda_gondola and proveedor_gondola == "Todos":
        st.warning("⚠️ Seleccioná un proveedor o escribí una búsqueda")
        st.stop()

    # ========================================================================
    # SECCIÓN 2: CARGAR DATOS
    # ========================================================================
    with st.spinner("Analizando productos..."):
        if df_todos_filtrado is None:
            df_todos_filtrado = get_todos_filtrados(fecha_desde_str, fecha_hasta_str, tiendas_tuple)

        df_base = df_filtrado.copy()

        if tienda_gondola != "Todas":
            df_base = df_base[df_base['Tienda'] == tienda_gondola]

        if proveedor_gondola != "Todos":
            df_base = df_base[df_base['Proveedor'] == proveedor_gondola]

        if busqueda_gondola:
            busqueda_lower = busqueda_gondola.lower()
            df_base = df_base[
                df_base['Descripcion'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df_base['Codigo'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
            ]

        if df_base.empty:
            st.warning("⚠️ No se encontraron productos")
            st.stop()

        # Abastecimiento
        df_abastecimiento = df_todos_filtrado[
            df_todos_filtrado['Tipo_Movimiento'].isin(['Recepción', 'Transferencia_Entrada'])
        ].copy()

        if tienda_gondola != "Todas":
            df_abastecimiento = df_abastecimiento[
                (df_abastecimiento['Tienda'] == tienda_gondola) |
                (df_abastecimiento['Tienda_Destino'] == tienda_gondola)
            ]

        if proveedor_gondola != "Todos":
            df_abastecimiento = df_abastecimiento[df_abastecimiento['Proveedor'] == proveedor_gondola]

        if busqueda_gondola:
            df_abastecimiento = df_abastecimiento[
                df_abastecimiento['Descripcion'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df_abastecimiento['Codigo'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
            ]

    # ========================================================================
    # SECCIÓN 3: CALCULAR MÉTRICAS
    # ========================================================================
    
    # Agrupar ventas
    df_productos = df_base.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
        'Venta_Total': 'sum',
        'Costo_Total': 'sum',
        'Margen': 'sum',
        'Cantidad': lambda x: abs(x).sum(),
        'Fecha': ['min', 'max', 'count']
    }).reset_index()

    df_productos.columns = [
        'Codigo', 'Descripcion', 'Proveedor',
        'Ventas', 'Costo', 'Margen', 'Unidades_Vendidas',
        'Primera_Venta', 'Ultima_Venta', 'Transacciones'
    ]

    # Métricas derivadas
    df_productos['Margen_Pct'] = (df_productos['Margen'] / df_productos['Ventas'] * 100).fillna(0)
    df_productos['Dias_Sin_Venta'] = (datetime.now() - pd.to_datetime(df_productos['Ultima_Venta'])).dt.days

    # Abastecimiento por producto
    if not df_abastecimiento.empty:
        abast_por_prod = df_abastecimiento.groupby('Codigo', observed=True).agg({
            'Fecha': 'max',
            'Cantidad': lambda x: abs(x).sum()
        }).reset_index()
        abast_por_prod.columns = ['Codigo', 'Ultima_Recepcion', 'Unidades_Recibidas']

        df_productos = df_productos.merge(abast_por_prod, on='Codigo', how='left')
        df_productos['Dias_Sin_Recepcion'] = (datetime.now() - pd.to_datetime(df_productos['Ultima_Recepcion'])).dt.days.fillna(999)
        df_productos['Unidades_Recibidas'] = df_productos['Unidades_Recibidas'].fillna(0)
    else:
        df_productos['Ultima_Recepcion'] = None
        df_productos['Unidades_Recibidas'] = 0
        df_productos['Dias_Sin_Recepcion'] = 999

    # Rotación = Vendido / Recibido
    df_productos['Rotacion'] = (
        df_productos['Unidades_Vendidas'] / df_productos['Unidades_Recibidas'].replace(0, 1)
    ).fillna(0)

    # Participación en ventas
    total_ventas = df_productos['Ventas'].sum()
    df_productos['Participacion_Pct'] = (df_productos['Ventas'] / total_ventas * 100).fillna(0)

    # Ranking por ventas
    df_productos['Ranking_Ventas'] = df_productos['Ventas'].rank(ascending=False, method='min')
    total_productos = len(df_productos)

    # ========================================================================
    # SECCIÓN 4: CLASIFICAR PARA GÓNDOLA (NUEVA LÓGICA)
    # ========================================================================
    
    rotacion_promedio = df_productos['Rotacion'].mean()
    margen_promedio = df_productos['Margen_Pct'].mean()
    top_20_pct = total_productos * 0.2

    def clasificar_gondola(row):
        """Clasifica el producto para decisión de góndola"""
        
        dias_sin_venta = row['Dias_Sin_Venta'] if pd.notna(row['Dias_Sin_Venta']) else 999
        dias_sin_recep = row['Dias_Sin_Recepcion'] if pd.notna(row['Dias_Sin_Recepcion']) else 999
        unidades_vendidas = row['Unidades_Vendidas'] if pd.notna(row['Unidades_Vendidas']) else 0
        unidades_recibidas = row['Unidades_Recibidas'] if pd.notna(row['Unidades_Recibidas']) else 0
        rotacion = row['Rotacion'] if pd.notna(row['Rotacion']) else 0
        ranking = row['Ranking_Ventas']
        margen = row['Margen_Pct']
        ventas = row['Ventas']
        participacion = row['Participacion_Pct']
        
        # =================================================================
        # REGLA 1: PROTEGER productos con buenas ventas o buen margen
        # =================================================================
        es_buen_vendedor = ventas > 50000  # Más de $50K en ventas
        es_rentable = margen >= 25  # Margen >= 25%
        es_top_20 = ranking <= (total_productos * 0.2)  # Top 20%
        
        # =================================================================
        # ⭐ DESTACAR: Top 5 + buen margen
        # =================================================================
        if ranking <= 5 and margen >= margen_promedio:
            return ('⭐ DESTACAR', 'Top 5 ventas + buen margen', '#10b981', 4)
        
        # =================================================================
        # ⬆️ AMPLIAR: Top 20% o muy buenas ventas o muy buen margen
        # =================================================================
        if es_top_20 and margen > 0:
            return ('⬆️ AMPLIAR', 'Top 20% en ventas', '#22d3ee', 3)
        
        if ventas > 100000 and margen > 0:
            return ('⬆️ AMPLIAR', 'Ventas altas', '#22d3ee', 3)
        
        if margen >= 30 and ventas > 30000:
            return ('⬆️ AMPLIAR', 'Margen excelente', '#22d3ee', 3)
        
        # =================================================================
        # ✅ MANTENER: Buen vendedor o rentable (PROTEGIDOS)
        # =================================================================
        if es_buen_vendedor or es_rentable:
            return ('✅ MANTENER', 'Buen rendimiento', '#6b7280', 2)
        
        # =================================================================
        # ❌ SACAR: Solo productos realmente muertos
        # =================================================================
        # Recibió mucho stock pero casi no vendió nada
        if unidades_recibidas > 30 and unidades_vendidas < 5 and dias_sin_recep < 60:
            return ('❌ SACAR', 'Recibió stock pero no vende', '#ef4444', 0)
        
        # Sin ventas hace mucho y vendió muy poco en total
        if dias_sin_venta > 45 and unidades_vendidas < 10 and ventas < 10000:
            return ('❌ SACAR', f'Sin ventas hace {int(dias_sin_venta)} días', '#ef4444', 0)
        
        # Ventas mínimas y margen negativo
        if ventas < 5000 and margen < 0:
            return ('❌ SACAR', 'Ventas mínimas + margen negativo', '#ef4444', 0)
        
        # =================================================================
        # ⬇️ REDUCIR: Solo productos con ventas bajas Y rotación baja
        # =================================================================
        if ventas < 20000 and rotacion < (rotacion_promedio * 0.3):
            return ('⬇️ REDUCIR', 'Ventas bajas + rotación baja', '#f97316', 1)
        
        if ventas < 15000 and margen < 10 and unidades_vendidas < 30:
            return ('⬇️ REDUCIR', 'Bajo rendimiento general', '#f97316', 1)
        
        # =================================================================
        # ✅ MANTENER: Todo lo demás
        # =================================================================
        return ('✅ MANTENER', 'Rendimiento normal', '#6b7280', 2)

    # Aplicar clasificación
    clasificaciones = df_productos.apply(clasificar_gondola, axis=1)
    df_productos['Accion'] = [c[0] for c in clasificaciones]
    df_productos['Motivo'] = [c[1] for c in clasificaciones]
    df_productos['Color'] = [c[2] for c in clasificaciones]
    df_productos['Frentes_Sugeridos'] = [c[3] for c in clasificaciones]

    # Ordenar por acción y ventas
    orden_accion = {'⭐ DESTACAR': 0, '⬆️ AMPLIAR': 1, '✅ MANTENER': 2, '⬇️ REDUCIR': 3, '❌ SACAR': 4}
    df_productos['Orden'] = df_productos['Accion'].map(orden_accion)
    df_productos = df_productos.sort_values(['Orden', 'Ventas'], ascending=[True, False])

    # ========================================================================
    # SECCIÓN 5: RESUMEN EJECUTIVO
    # ========================================================================
    st.markdown("---")
    st.markdown("### 📊 Resumen de Optimización")

    # Contar por acción
    conteo_acciones = df_productos['Accion'].value_counts()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        n_destacar = conteo_acciones.get('⭐ DESTACAR', 0)
        st.markdown(f'''
        <div class="card" style="border-color: #10b981;">
            <div class="metric-label" style="color: #10b981;">⭐ DESTACAR</div>
            <div class="metric-value">{n_destacar}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        n_ampliar = conteo_acciones.get('⬆️ AMPLIAR', 0)
        st.markdown(f'''
        <div class="card" style="border-color: #22d3ee;">
            <div class="metric-label" style="color: #22d3ee;">⬆️ AMPLIAR</div>
            <div class="metric-value">{n_ampliar}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        n_mantener = conteo_acciones.get('✅ MANTENER', 0)
        st.markdown(f'''
        <div class="card" style="border-color: #6b7280;">
            <div class="metric-label" style="color: #6b7280;">✅ MANTENER</div>
            <div class="metric-value">{n_mantener}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        n_reducir = conteo_acciones.get('⬇️ REDUCIR', 0)
        st.markdown(f'''
        <div class="card" style="border-color: #f97316;">
            <div class="metric-label" style="color: #f97316;">⬇️ REDUCIR</div>
            <div class="metric-value">{n_reducir}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        n_sacar = conteo_acciones.get('❌ SACAR', 0)
        st.markdown(f'''
        <div class="card" style="border-color: #ef4444;">
            <div class="metric-label" style="color: #ef4444;">❌ SACAR</div>
            <div class="metric-value">{n_sacar}</div>
        </div>
        ''', unsafe_allow_html=True)

    # Impacto estimado
    ventas_a_sacar = df_productos[df_productos['Accion'] == '❌ SACAR']['Ventas'].sum()
    ventas_a_ampliar = df_productos[df_productos['Accion'].isin(['⭐ DESTACAR', '⬆️ AMPLIAR'])]['Ventas'].sum()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"""
        **🎯 Productos a potenciar:** {n_destacar + n_ampliar}  
        **💰 Ventas actuales:** {format_currency(ventas_a_ampliar)}  
        **📈 Potencial si amplías:** +10-20% estimado
        """)
    
    with col2:
        st.error(f"""
        **🗑️ Productos a sacar/reducir:** {n_sacar + n_reducir}  
        **💸 Ventas que representan:** {format_currency(ventas_a_sacar)}  
        **📦 Espacio que liberás:** ~{n_sacar + n_reducir} frentes
        """)

    # ========================================================================
    # SECCIÓN 6: RECOMENDACIONES DETALLADAS
    # ========================================================================
    st.markdown("---")
    st.markdown("### 🎯 Plan de Acción")

    # DESTACAR
    df_destacar = df_productos[df_productos['Accion'] == '⭐ DESTACAR']
    if not df_destacar.empty:
        with st.expander(f"⭐ DESTACAR - Punta de góndola ({len(df_destacar)} productos)", expanded=True):
            st.success("**Mejor ubicación + máximo espacio** → Son tus productos estrella")
            for _, row in df_destacar.iterrows():
                st.markdown(f"""
                - **{row['Descripcion'][:50]}**  
                  Ventas: {format_currency(row['Ventas'])} | Margen: {row['Margen_Pct']:.1f}% | Rotación: {row['Rotacion']:.1f}x
                """)

    # AMPLIAR
    df_ampliar = df_productos[df_productos['Accion'] == '⬆️ AMPLIAR']
    if not df_ampliar.empty:
        with st.expander(f"⬆️ AMPLIAR - Más espacio ({len(df_ampliar)} productos)", expanded=True):
            st.info("**Duplicar frentes** → Alta demanda, no pueden faltar")
            for _, row in df_ampliar.head(10).iterrows():
                st.markdown(f"""
                - **{row['Descripcion'][:50]}**  
                  Ventas: {format_currency(row['Ventas'])} | {int(row['Unidades_Vendidas'])} uds vendidas
                """)
            if len(df_ampliar) > 10:
                st.caption(f"... y {len(df_ampliar) - 10} productos más")

    # REDUCIR
    df_reducir = df_productos[df_productos['Accion'] == '⬇️ REDUCIR']
    if not df_reducir.empty:
        with st.expander(f"⬇️ REDUCIR - Dejar 1 frente ({len(df_reducir)} productos)", expanded=False):
            st.warning("**Minimizar espacio** → Baja rotación, solo para tener variedad")
            for _, row in df_reducir.head(10).iterrows():
                st.markdown(f"""
                - **{row['Descripcion'][:50]}**  
                  Motivo: {row['Motivo']} | Rotación: {row['Rotacion']:.2f}x
                """)

    # SACAR
    df_sacar = df_productos[df_productos['Accion'] == '❌ SACAR']
    if not df_sacar.empty:
        with st.expander(f"❌ SACAR de góndola ({len(df_sacar)} productos)", expanded=True):
            st.error("**Eliminar** → Ocupan espacio sin generar ventas")
            for _, row in df_sacar.iterrows():
                recibido = int(row['Unidades_Recibidas']) if pd.notna(row['Unidades_Recibidas']) else 0
                vendido = int(row['Unidades_Vendidas']) if pd.notna(row['Unidades_Vendidas']) else 0
                st.markdown(f"""
                - **{row['Descripcion'][:50]}**  
                  Recibió: {recibido} uds | Vendió: {vendido} uds | {row['Motivo']}
                """)

    # ========================================================================
    # SECCIÓN 7: TABLA COMPLETA
    # ========================================================================
    st.markdown("---")
    st.markdown("### 📋 Detalle Completo")

    # Filtro por acción
    filtro_accion = st.multiselect(
        "Filtrar por acción:",
        options=['⭐ DESTACAR', '⬆️ AMPLIAR', '✅ MANTENER', '⬇️ REDUCIR', '❌ SACAR'],
        default=['⭐ DESTACAR', '⬆️ AMPLIAR', '⬇️ REDUCIR', '❌ SACAR'],
        key="filtro_accion_gondola"
    )

    df_mostrar = df_productos[df_productos['Accion'].isin(filtro_accion)].copy()

    # Formatear
    df_mostrar['Ventas_Fmt'] = df_mostrar['Ventas'].apply(format_currency)
    df_mostrar['Margen_Fmt'] = df_mostrar['Margen_Pct'].apply(lambda x: f"{x:.1f}%")
    df_mostrar['Rotacion_Fmt'] = df_mostrar['Rotacion'].apply(lambda x: f"{x:.2f}x")
    df_mostrar['Vendidas'] = df_mostrar['Unidades_Vendidas'].fillna(0).astype(int)
    df_mostrar['Recibidas'] = df_mostrar['Unidades_Recibidas'].fillna(0).astype(int)

    st.dataframe(
        df_mostrar[[
            'Accion', 'Codigo', 'Descripcion', 
            'Ventas_Fmt', 'Margen_Fmt', 'Vendidas', 'Recibidas', 'Rotacion_Fmt', 'Motivo'
        ]].rename(columns={
            'Accion': 'Acción',
            'Ventas_Fmt': 'Ventas',
            'Margen_Fmt': 'Margen',
            'Rotacion_Fmt': 'Rotación'
        }),
        use_container_width=True,
        height=400,
        hide_index=True
    )

    # ========================================================================
    # SECCIÓN 8: EXPORTAR
    # ========================================================================
    st.markdown("---")
    st.markdown("### 📥 Exportar Plan de Acción")

    col1, col2, col3 = st.columns(3)

    with col1:
        df_export_completo = df_productos[[
            'Accion', 'Codigo', 'Descripcion', 'Proveedor',
            'Ventas', 'Margen_Pct', 'Unidades_Vendidas', 'Unidades_Recibidas',
            'Rotacion', 'Dias_Sin_Venta', 'Dias_Sin_Recepcion', 'Motivo', 'Frentes_Sugeridos'
        ]].copy()

        excel_completo = to_excel(df_export_completo)
        st.download_button(
            label="📥 Plan Completo",
            data=excel_completo,
            file_name=f"plan_gondola_{proveedor_gondola}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col2:
        df_export_sacar = df_productos[df_productos['Accion'] == '❌ SACAR'][[
            'Codigo', 'Descripcion', 'Proveedor', 'Unidades_Vendidas', 'Unidades_Recibidas', 'Motivo'
        ]]

        if not df_export_sacar.empty:
            excel_sacar = to_excel(df_export_sacar)
            st.download_button(
                label="❌ Lista para SACAR",
                data=excel_sacar,
                file_name=f"sacar_gondola_{proveedor_gondola}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button("❌ Sin productos para sacar", disabled=True, use_container_width=True)

    with col3:
        df_export_ampliar = df_productos[df_productos['Accion'].isin(['⭐ DESTACAR', '⬆️ AMPLIAR'])][[
            'Codigo', 'Descripcion', 'Proveedor', 'Ventas', 'Margen_Pct', 'Frentes_Sugeridos'
        ]]

        if not df_export_ampliar.empty:
            excel_ampliar = to_excel(df_export_ampliar)
            st.download_button(
                label="⬆️ Lista para AMPLIAR",
                data=excel_ampliar,
                file_name=f"ampliar_gondola_{proveedor_gondola}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button("⬆️ Sin productos para ampliar", disabled=True, use_container_width=True)
# ============================================================================
# 💰 SIMULADOR DE RENTABILIDAD - MÓDULO PARA AGREGAR A Appgeneral.py
# ============================================================================
# 
# INSTRUCCIONES:
# 1. Agregar "💰 Simulador Pricing" a la lista del radio en el sidebar
# 2. Copiar todo este código antes del footer final de Appgeneral.py
#
# ============================================================================

elif pagina == "📈 Ventas 360":
    st.markdown('<h1 class="main-header">📈 Ventas 360</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Vista ejecutiva y accionable de ventas, margen y rentabilidad</p>', unsafe_allow_html=True)
    st.markdown("---")

    if df_filtrado is None or df_filtrado.empty:
        st.warning("⚠️ No hay datos de ventas para analizar")
        st.stop()

    # Filtros locales
    st.markdown("### 🔍 Filtros de Ventas")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tiendas_disponibles = sorted(df_filtrado['Tienda'].dropna().unique().tolist())
        tienda_ventas = st.multiselect(
            "🏪 Tienda(s)",
            options=tiendas_disponibles,
            default=[],
            key="filtro_tienda_ventas_360",
            help="Dejar vacío para todas"
        )

    with col2:
        proveedores_disponibles = sorted(df_filtrado['Proveedor'].dropna().unique().tolist())
        proveedor_ventas = st.multiselect(
            "🏭 Proveedor(es)",
            options=proveedores_disponibles,
            default=[],
            key="filtro_proveedor_ventas_360",
            help="Dejar vacío para todos"
        )

    with col3:
        buscar_producto = st.text_input(
            "🔍 Buscar producto",
            placeholder="Escribí para filtrar...",
            key="buscar_producto_ventas_360"
        )
        opciones_prod = df_productos_lista.copy()
        if buscar_producto:
            opciones_prod = opciones_prod[
                opciones_prod['display'].str.contains(buscar_producto, case=False, na=False)
            ]
        productos_sel = st.multiselect(
            "Producto(s)",
            options=opciones_prod['display'].tolist(),
            default=[],
            key="productos_sel_ventas_360"
        )

    with col4:
        top_n = st.number_input(
            "Top N",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            key="top_n_ventas_360"
        )

    # Filtro de fechas local (dentro de Ventas 360)
    fecha_min_ventas = pd.to_datetime(df_filtrado['Fecha']).min().date()
    fecha_max_ventas = pd.to_datetime(df_filtrado['Fecha']).max().date()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_360_desde = st.date_input(
            "Desde (Ventas 360)",
            value=max(fecha_min_ventas, fecha_desde),
            min_value=fecha_min_ventas,
            max_value=fecha_max_ventas,
            format="DD/MM/YYYY",
            key="fecha_360_desde"
        )
    with col_f2:
        fecha_360_hasta = st.date_input(
            "Hasta (Ventas 360)",
            value=min(fecha_max_ventas, fecha_hasta),
            min_value=fecha_min_ventas,
            max_value=fecha_max_ventas,
            format="DD/MM/YYYY",
            key="fecha_360_hasta"
        )

    df_ventas = df_filtrado.copy()

    if tienda_ventas:
        df_ventas = df_ventas[df_ventas['Tienda'].isin(tienda_ventas)]
    if proveedor_ventas:
        df_ventas = df_ventas[df_ventas['Proveedor'].isin(proveedor_ventas)]
    if productos_sel:
        codigos_sel = [p.split(" - ")[0] for p in productos_sel]
        df_ventas = df_ventas[df_ventas['Codigo'].isin(codigos_sel)]
    df_ventas = df_ventas[(df_ventas['Fecha'].dt.date >= fecha_360_desde) & (df_ventas['Fecha'].dt.date <= fecha_360_hasta)]

    if df_ventas.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
        st.stop()

    # KPIs
    venta_total = df_ventas['Venta_Total'].sum()
    costo_total = df_ventas['Costo_Total'].sum()
    margen_total = df_ventas['Margen'].sum()
    margen_pct = (margen_total / costo_total * 100) if costo_total > 0 else 0
    unidades = df_ventas['Cantidad'].abs().sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">VENTAS</div>
            <div class="metric-value" style="color:#60a5fa;">{format_currency(venta_total)}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">COSTO</div>
            <div class="metric-value" style="color:#f97316;">{format_currency(costo_total)}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">MARGEN $</div>
            <div class="metric-value" style="color:#10b981;">{format_currency(margen_total)}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col4:
        color_margen = '#10b981' if margen_pct >= 20 else '#f97316' if margen_pct >= 10 else '#ef4444'
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">MARGEN %</div>
            <div class="metric-value" style="color:{color_margen};">{margen_pct:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)

    with col5:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">UNIDADES</div>
            <div class="metric-value">{format_number(unidades)}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("---")

    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Resumen",
        "🚨 Alertas",
        "🧾 Productos",
        "🏪 Tiendas",
        "🏭 Proveedores",
        "📥 Exportar"
    ])

    with tab1:
        st.markdown("### Evolución y distribución")

        df_dia = df_ventas.copy()
        df_dia['Fecha'] = pd.to_datetime(df_dia['Fecha'])
        df_dia = df_dia.groupby(df_dia['Fecha'].dt.date, observed=True).agg({
            'Venta_Total': 'sum',
            'Margen': 'sum',
            'Costo_Total': 'sum'
        }).reset_index()
        df_dia['Margen_Pct'] = (df_dia['Margen'] / df_dia['Costo_Total'] * 100).replace([pd.NA, pd.NaT], 0).fillna(0)

        col1, col2 = st.columns(2)

        with col1:
            fig_ventas = px.line(
                df_dia,
                x='Fecha',
                y='Venta_Total',
                title='Ventas diarias',
                labels={'Venta_Total': 'Ventas $', 'Fecha': ''}
            )
            fig_ventas.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ventas, use_container_width=True)

        with col2:
            fig_margen = px.line(
                df_dia,
                x='Fecha',
                y='Margen_Pct',
                title='Margen % diario',
                labels={'Margen_Pct': 'Margen %', 'Fecha': ''}
            )
            fig_margen.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_margen, use_container_width=True)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            df_tienda = df_ventas.groupby('Tienda', observed=True)['Venta_Total'].sum().reset_index().sort_values('Venta_Total', ascending=False).head(top_n)
            fig_tienda = px.bar(
                df_tienda,
                x='Venta_Total',
                y='Tienda',
                orientation='h',
                title=f'Top {top_n} Tiendas por Ventas',
                labels={'Venta_Total': 'Ventas $', 'Tienda': ''}
            )
            fig_tienda.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_tienda, use_container_width=True)

        with col2:
            df_prov = df_ventas.groupby('Proveedor', observed=True)['Venta_Total'].sum().reset_index().sort_values('Venta_Total', ascending=False).head(top_n)
            fig_prov = px.bar(
                df_prov,
                x='Venta_Total',
                y='Proveedor',
                orientation='h',
                title=f'Top {top_n} Proveedores por Ventas',
                labels={'Venta_Total': 'Ventas $', 'Proveedor': ''}
            )
            fig_prov.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_prov, use_container_width=True)

        st.markdown("---")
        st.markdown("### Comparación mes a mes (YoY)")

        df_mes = df_ventas.copy()
        df_mes['Fecha'] = pd.to_datetime(df_mes['Fecha'])
        df_mes['Año'] = df_mes['Fecha'].dt.year
        df_mes['Mes'] = df_mes['Fecha'].dt.month

        df_mes = df_mes.groupby(['Año', 'Mes'], observed=True).agg({
            'Venta_Total': 'sum',
            'Margen': 'sum',
            'Costo_Total': 'sum'
        }).reset_index()
        df_mes['Margen_Pct'] = (
            df_mes['Margen'] / df_mes['Costo_Total'].replace(0, pd.NA) * 100
        ).fillna(0)

        metric_opt = st.selectbox(
            "Métrica",
            options=["Ventas $", "Margen $", "Margen %"],
            key="metric_yoy_ventas_360"
        )

        metric_map = {
            "Ventas $": "Venta_Total",
            "Margen $": "Margen",
            "Margen %": "Margen_Pct",
        }
        metric_col = metric_map[metric_opt]

        years = sorted(df_mes['Año'].unique().tolist())
        year_sel = st.selectbox(
            "Año",
            options=years,
            index=len(years) - 1 if years else 0,
            key="year_yoy_ventas_360"
        )

        fig_yoy = px.line(
            df_mes,
            x='Mes',
            y=metric_col,
            color='Año',
            markers=True,
            title=f"{metric_opt} por mes (comparación anual)",
            labels={'Mes': 'Mes', metric_col: metric_opt, 'Año': 'Año'}
        )
        fig_yoy.update_layout(height=380, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_yoy.update_xaxes(tickmode='array', tickvals=list(range(1, 13)))
        st.plotly_chart(fig_yoy, use_container_width=True)

        if year_sel and (year_sel - 1) in years:
            df_piv = df_mes[df_mes['Año'].isin([year_sel, year_sel - 1])].pivot_table(
                index='Mes',
                columns='Año',
                values=metric_col,
                aggfunc='sum'
            ).reset_index()
            df_piv['Var_%'] = (
                (df_piv[year_sel] - df_piv[year_sel - 1]) / df_piv[year_sel - 1].replace(0, pd.NA) * 100
            ).fillna(0)

            st.dataframe(
                df_piv,
                use_container_width=True,
                height=300,
                column_config={
                    'Mes': st.column_config.NumberColumn(format="%d"),
                    year_sel: st.column_config.NumberColumn(format="$%.0f" if metric_col != 'Margen_Pct' else "%.1f%%"),
                    year_sel - 1: st.column_config.NumberColumn(format="$%.0f" if metric_col != 'Margen_Pct' else "%.1f%%"),
                    'Var_%': st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

            excel_yoy = to_excel(df_piv)
            st.download_button(
                label="📥 Exportar comparación YoY",
                data=excel_yoy,
                file_name=f"comparacion_yoy_{year_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with tab2:
        st.markdown("### Pareto de pérdidas (margen negativo)")

        df_productos = df_ventas.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
            'Cantidad': lambda x: abs(x).sum(),
            'Costo': 'mean',
            'Precio_Venta': 'mean',
            'Venta_Total': 'sum',
            'Costo_Total': 'sum',
            'Margen': 'sum'
        }).reset_index()

        df_productos['Margen_Pct'] = (
            (df_productos['Precio_Venta'] - df_productos['Costo']) /
            df_productos['Costo'].replace(0, pd.NA) * 100
        ).fillna(0)

        df_neg = df_productos[df_productos['Margen_Pct'] < 0].copy()
        df_neg = df_neg.sort_values('Margen', ascending=True)

        if df_neg.empty:
            st.success("✅ No hay productos con margen negativo")
        else:
            df_neg['Perdida'] = df_neg['Margen'].abs()
            df_neg['Perdida_Acum'] = df_neg['Perdida'].cumsum()
            total_perdida = df_neg['Perdida'].sum()
            df_neg['Perdida_Acum_Pct'] = (df_neg['Perdida_Acum'] / total_perdida * 100).fillna(0)

            fig_pareto = px.bar(
                df_neg.head(top_n),
                x='Descripcion',
                y='Perdida',
                title=f'Pareto de pérdidas (Top {top_n})',
                labels={'Perdida': 'Pérdida $', 'Descripcion': ''}
            )
            fig_pareto.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pareto, use_container_width=True)

            df_neg_display = df_neg[[
                'Codigo', 'Descripcion', 'Proveedor', 'Costo', 'Precio_Venta', 'Margen_Pct', 'Cantidad', 'Margen'
            ]].head(200).copy()

            df_neg_display.rename(columns={
                'Costo': 'Costo_Unitario',
                'Precio_Venta': 'Precio_Unitario',
                'Cantidad': 'Unidades',
                'Margen': 'Perdida_Total'
            }, inplace=True)

            st.dataframe(
                df_neg_display,
                use_container_width=True,
                height=400
            )

            excel_neg = to_excel(df_neg_display)
            st.download_button(
                label="📥 Exportar Margen Negativo",
                data=excel_neg,
                file_name=f"margen_negativo_ventas_360_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with tab3:
        st.markdown("### Productos")

        df_prod = df_ventas.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
            'Cantidad': lambda x: abs(x).sum(),
            'Costo_Total': 'sum',
            'Costo': 'mean',
            'Venta_Total': 'sum',
            'Margen': 'sum'
        }).reset_index()

        df_prod['Unidades'] = df_prod['Cantidad']
        unidades_totales = df_prod['Unidades'].sum()
        df_prod['Rotacion_Pct'] = (df_prod['Unidades'] / unidades_totales * 100).fillna(0)
        df_prod['Precio_Unitario'] = (
            df_prod['Venta_Total'] / df_prod['Unidades'].replace(0, pd.NA)
        ).fillna(0)
        df_prod['Margen_Pct'] = (
            df_prod['Margen'] / df_prod['Costo_Total'].replace(0, pd.NA) * 100
        ).fillna(0)

        tab_top, tab_margen, tab_bottom, tab_neg, tab_scatter = st.tabs([
            "🏆 Top Ventas", "📈 Top Margen", "🔻 Bottom Margen", "🚨 Margen Negativo", "🧪 Dispersión"
        ])

        with tab_top:
            df_top = df_prod.sort_values('Venta_Total', ascending=False).head(200)
            st.dataframe(
                df_top[[
                    'Codigo', 'Descripcion', 'Proveedor', 'Unidades', 'Rotacion_Pct',
                    'Costo', 'Precio_Unitario', 'Venta_Total', 'Margen', 'Margen_Pct'
                ]],
                use_container_width=True,
                height=500,
                column_config={
                    'Unidades': st.column_config.NumberColumn(format="%.0f"),
                    'Rotacion_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    'Costo': st.column_config.NumberColumn(format="$%.2f"),
                    'Precio_Unitario': st.column_config.NumberColumn(format="$%.2f"),
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

        with tab_margen:
            df_top_margen = df_prod.sort_values('Margen_Pct', ascending=False).head(200)
            st.dataframe(
                df_top_margen[[
                    'Codigo', 'Descripcion', 'Proveedor', 'Unidades', 'Rotacion_Pct',
                    'Costo', 'Precio_Unitario', 'Venta_Total', 'Margen', 'Margen_Pct'
                ]],
                use_container_width=True,
                height=500,
                column_config={
                    'Unidades': st.column_config.NumberColumn(format="%.0f"),
                    'Rotacion_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    'Costo': st.column_config.NumberColumn(format="$%.2f"),
                    'Precio_Unitario': st.column_config.NumberColumn(format="$%.2f"),
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

        with tab_bottom:
            df_bottom = df_prod.sort_values('Margen_Pct', ascending=True).head(200)
            st.dataframe(
                df_bottom[[
                    'Codigo', 'Descripcion', 'Proveedor', 'Unidades', 'Rotacion_Pct',
                    'Costo', 'Precio_Unitario', 'Venta_Total', 'Margen', 'Margen_Pct'
                ]],
                use_container_width=True,
                height=500,
                column_config={
                    'Unidades': st.column_config.NumberColumn(format="%.0f"),
                    'Rotacion_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    'Costo': st.column_config.NumberColumn(format="$%.2f"),
                    'Precio_Unitario': st.column_config.NumberColumn(format="$%.2f"),
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                    'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

        with tab_neg:
            df_neg_prod = df_prod[df_prod['Margen_Pct'] < 0].sort_values('Margen_Pct').head(200)
            if df_neg_prod.empty:
                st.success("✅ No hay productos con margen negativo")
            else:
                st.dataframe(
                    df_neg_prod[[
                        'Codigo', 'Descripcion', 'Proveedor', 'Unidades', 'Rotacion_Pct',
                        'Costo', 'Precio_Unitario', 'Venta_Total', 'Margen', 'Margen_Pct'
                    ]],
                    use_container_width=True,
                    height=500,
                    column_config={
                        'Unidades': st.column_config.NumberColumn(format="%.0f"),
                        'Rotacion_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                        'Costo': st.column_config.NumberColumn(format="$%.2f"),
                        'Precio_Unitario': st.column_config.NumberColumn(format="$%.2f"),
                        'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                        'Margen': st.column_config.NumberColumn(format="$%.0f"),
                        'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                    }
                )

        with tab_scatter:
            st.markdown("#### Precio vs Margen % (tamaño = unidades)")
            fig_scatter = px.scatter(
                df_prod,
                x='Precio_Unitario',
                y='Margen_Pct',
                size='Unidades',
                color='Proveedor',
                hover_data=['Codigo', 'Descripcion', 'Venta_Total', 'Margen'],
                title='Dispersión Precio vs Margen %'
            )
            fig_scatter.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("---")
        st.markdown("### Ventas por tienda de un producto/proveedor")

        col_f1, col_f2 = st.columns(2)

        with col_f1:
            proveedor_foco = st.selectbox(
                "Proveedor",
                options=["Todos"] + sorted(df_ventas['Proveedor'].dropna().unique().tolist()),
                key="proveedor_foco_360"
            )

        df_opciones = df_ventas.copy()
        if proveedor_foco != "Todos":
            df_opciones = df_opciones[df_opciones['Proveedor'] == proveedor_foco]

        df_opciones = df_opciones[['Codigo', 'Descripcion']].dropna().drop_duplicates()
        df_opciones['display'] = df_opciones['Codigo'].astype(str) + " - " + df_opciones['Descripcion'].astype(str)

        with col_f2:
            producto_foco = st.selectbox(
                "Producto",
                options=df_opciones['display'].tolist(),
                key="producto_foco_360"
            )

        if producto_foco:
            codigo_sel = producto_foco.split(" - ")[0]
            df_focus = df_ventas[df_ventas['Codigo'].astype(str) == str(codigo_sel)].copy()
            if proveedor_foco != "Todos":
                df_focus = df_focus[df_focus['Proveedor'] == proveedor_foco]

            df_focus_tienda = df_focus.groupby('Tienda', observed=True).agg({
                'Venta_Total': 'sum',
                'Cantidad': lambda x: abs(x).sum(),
                'Margen': 'sum'
            }).reset_index().sort_values('Venta_Total', ascending=False)

            fig_focus = px.bar(
                df_focus_tienda,
                x='Venta_Total',
                y='Tienda',
                orientation='h',
                title='Ventas por tienda',
                labels={'Venta_Total': 'Ventas $', 'Tienda': ''}
            )
            fig_focus.update_layout(height=420, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_focus, use_container_width=True)

            st.dataframe(
                df_focus_tienda,
                use_container_width=True,
                height=350,
                column_config={
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Cantidad': st.column_config.NumberColumn(format="%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                }
            )

            excel_focus = to_excel(df_focus_tienda)
            st.download_button(
                label="📥 Exportar ventas por tienda",
                data=excel_focus,
                file_name=f"ventas_tienda_{codigo_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_prod = to_excel(df_prod)
        st.download_button(
            label="📥 Exportar Productos (Detalle)",
            data=excel_prod,
            file_name=f"ranking_productos_ventas_360_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with tab4:
        st.markdown("### Tiendas")

        df_tiendas_det = df_ventas.groupby('Tienda', observed=True).agg({
            'Venta_Total': 'sum',
            'Costo_Total': 'sum',
            'Margen': 'sum',
            'Cantidad': lambda x: abs(x).sum()
        }).reset_index()
        df_tiendas_det['Margen_Pct'] = (
            df_tiendas_det['Margen'] / df_tiendas_det['Costo_Total'].replace(0, pd.NA) * 100
        ).fillna(0)

        df_tiendas_det = df_tiendas_det.sort_values('Venta_Total', ascending=False)

        st.dataframe(
            df_tiendas_det,
            use_container_width=True,
            height=420,
            column_config={
                'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                'Costo_Total': st.column_config.NumberColumn(format="$%.0f"),
                'Margen': st.column_config.NumberColumn(format="$%.0f"),
                'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                'Cantidad': st.column_config.NumberColumn(format="%.0f"),
            }
        )

        st.markdown("---")
        st.markdown("#### Top productos por tienda")
        tienda_sel = st.selectbox(
            "Seleccionar tienda",
            options=df_tiendas_det['Tienda'].tolist(),
            index=0 if not df_tiendas_det.empty else None,
            key="tienda_top_productos_360"
        )

        if tienda_sel:
            df_top_tienda = df_ventas[df_ventas['Tienda'] == tienda_sel].groupby(
                ['Codigo', 'Descripcion', 'Proveedor'], observed=True
            ).agg({
                'Venta_Total': 'sum',
                'Cantidad': lambda x: abs(x).sum(),
                'Margen': 'sum'
            }).reset_index().sort_values('Venta_Total', ascending=False).head(top_n)

            st.dataframe(
                df_top_tienda,
                use_container_width=True,
                height=350,
                column_config={
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Cantidad': st.column_config.NumberColumn(format="%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                }
            )

            excel_tienda = to_excel(df_top_tienda)
            st.download_button(
                label="📥 Exportar Top productos (Tienda)",
                data=excel_tienda,
                file_name=f"top_productos_tienda_{tienda_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_tiendas = to_excel(df_tiendas_det)
        st.download_button(
            label="📥 Exportar detalle por tienda",
            data=excel_tiendas,
            file_name=f"detalle_tiendas_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with tab5:
        st.markdown("### Proveedores")

        df_prov_det = df_ventas.groupby('Proveedor', observed=True).agg({
            'Venta_Total': 'sum',
            'Costo_Total': 'sum',
            'Margen': 'sum',
            'Cantidad': lambda x: abs(x).sum()
        }).reset_index()
        df_prov_det['Margen_Pct'] = (
            df_prov_det['Margen'] / df_prov_det['Costo_Total'].replace(0, pd.NA) * 100
        ).fillna(0)

        df_prov_det = df_prov_det.sort_values('Venta_Total', ascending=False)

        st.dataframe(
            df_prov_det.head(200),
            use_container_width=True,
            height=420,
            column_config={
                'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                'Costo_Total': st.column_config.NumberColumn(format="$%.0f"),
                'Margen': st.column_config.NumberColumn(format="$%.0f"),
                'Margen_Pct': st.column_config.NumberColumn(format="%.1f%%"),
                'Cantidad': st.column_config.NumberColumn(format="%.0f"),
            }
        )

        st.markdown("---")
        st.markdown("#### Top productos por proveedor")
        proveedor_sel = st.selectbox(
            "Seleccionar proveedor",
            options=df_prov_det['Proveedor'].tolist(),
            index=0 if not df_prov_det.empty else None,
            key="proveedor_top_productos_360"
        )

        if proveedor_sel:
            df_top_prov = df_ventas[df_ventas['Proveedor'] == proveedor_sel].groupby(
                ['Codigo', 'Descripcion', 'Tienda'], observed=True
            ).agg({
                'Venta_Total': 'sum',
                'Cantidad': lambda x: abs(x).sum(),
                'Margen': 'sum'
            }).reset_index().sort_values('Venta_Total', ascending=False).head(top_n)

            st.dataframe(
                df_top_prov,
                use_container_width=True,
                height=350,
                column_config={
                    'Venta_Total': st.column_config.NumberColumn(format="$%.0f"),
                    'Cantidad': st.column_config.NumberColumn(format="%.0f"),
                    'Margen': st.column_config.NumberColumn(format="$%.0f"),
                }
            )

            excel_prov = to_excel(df_top_prov)
            st.download_button(
                label="📥 Exportar Top productos (Proveedor)",
                data=excel_prov,
                file_name=f"top_productos_proveedor_{proveedor_sel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        excel_proveedores = to_excel(df_prov_det)
        st.download_button(
            label="📥 Exportar detalle por proveedor",
            data=excel_proveedores,
            file_name=f"detalle_proveedores_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with tab6:
        st.markdown("### Exportaciones rápidas")

        excel_ventas = to_excel(df_ventas)
        st.download_button(
            label="📥 Exportar Ventas Filtradas",
            data=excel_ventas,
            file_name=f"ventas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")

elif pagina == "💰 Simulador Pricing":
    st.markdown('<h1 class="main-header">💰 Simulador de Rentabilidad</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Optimiza precios para alcanzar tu objetivo de margen sin afectar productos ancla</p>', unsafe_allow_html=True)
    st.markdown("---")

    # ========================================================================
    # FILTROS DE TIENDA Y PROVEEDOR
    # ========================================================================
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro de Tienda
        tiendas_disponibles = sorted(df_filtrado['Tienda'].dropna().unique().tolist()) if df_filtrado is not None else []
        tienda_pricing = st.multiselect(
            "🏪 Tienda(s)",
            options=tiendas_disponibles,
            default=[],
            key="filtro_tienda_pricing",
            help="Dejar vacío para todas las tiendas"
        )
    
    with col2:
        # Filtro de Proveedor
        proveedores_disponibles = sorted(df_filtrado['Proveedor'].dropna().unique().tolist()) if df_filtrado is not None else []
        proveedor_pricing = st.multiselect(
            "🏭 Proveedor(es)",
            options=proveedores_disponibles,
            default=[],
            key="filtro_proveedor_pricing",
            help="Dejar vacío para todos los proveedores"
        )
    
    with col3:
        # Búsqueda por producto
        buscar_producto_pricing = st.text_input(
            "🔍 Buscar Producto",
            placeholder="Código o descripción...",
            key="buscar_producto_pricing"
        )
    
    st.markdown("---")

    # ========================================================================
    # CARGAR Y PREPARAR DATOS
    # ========================================================================
    
    # Usar df_filtrado que ya tiene las ventas
    if df_filtrado is None or df_filtrado.empty:
        st.warning("⚠️ No hay datos de ventas para analizar")
        st.stop()
    
    # Aplicar filtros
    df_pricing_base = df_filtrado.copy()
    
    # Filtro de tienda
    if tienda_pricing:
        df_pricing_base = df_pricing_base[df_pricing_base['Tienda'].isin(tienda_pricing)]
    
    # Filtro de proveedor
    if proveedor_pricing:
        df_pricing_base = df_pricing_base[df_pricing_base['Proveedor'].isin(proveedor_pricing)]
    
    # Filtro de búsqueda de producto
    if buscar_producto_pricing:
        df_pricing_base = df_pricing_base[
            df_pricing_base['Codigo'].astype(str).str.contains(buscar_producto_pricing, case=False, na=False) |
            df_pricing_base['Descripcion'].astype(str).str.contains(buscar_producto_pricing, case=False, na=False)
        ]
    
    if df_pricing_base.empty:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
        st.stop()
    
    # Mostrar resumen de filtros aplicados
    filtros_aplicados = []
    if tienda_pricing:
        filtros_aplicados.append(f"🏪 {len(tienda_pricing)} tienda(s)")
    if proveedor_pricing:
        filtros_aplicados.append(f"🏭 {len(proveedor_pricing)} proveedor(es)")
    if buscar_producto_pricing:
        filtros_aplicados.append(f"🔍 '{buscar_producto_pricing}'")
    
    if filtros_aplicados:
        st.info(f"Filtros activos: {' | '.join(filtros_aplicados)} → **{len(df_pricing_base):,} registros**")
    
    # Calcular precio unitario desde el total y la cantidad
    if 'Precio_Venta' in df_pricing_base.columns and 'Cantidad' in df_pricing_base.columns:
        cantidad_abs = df_pricing_base['Cantidad'].abs().replace(0, pd.NA)
        df_pricing_base['Precio_Unitario'] = (df_pricing_base['Precio_Venta'] / cantidad_abs)
    else:
        df_pricing_base['Precio_Unitario'] = pd.NA

    # Agrupar por producto para análisis
    df_productos_precio = df_pricing_base.groupby(['Codigo', 'Descripcion', 'Proveedor'], observed=True).agg({
        'Cantidad': lambda x: abs(x).sum(),
        'Costo': 'mean',
        'Precio_Unitario': 'mean',
        'Venta_Total': 'sum',
        'Costo_Total': 'sum',
        'Margen': 'sum'
    }).reset_index()
    
    df_productos_precio.columns = [
        'Codigo', 'Descripcion', 'Proveedor',
        'Unidades_Vendidas', 'Costo_Promedio', 'Precio_Actual',
        'Venta_Total', 'Costo_Total', 'Margen_Total'
    ]
    
    # Calcular métricas - Margen sobre COSTO (markup)
    costo_safe = df_productos_precio['Costo_Promedio'].replace(0, pd.NA)
    df_productos_precio['Margen_Pct'] = (
        (df_productos_precio['Precio_Actual'] - df_productos_precio['Costo_Promedio']) / 
        costo_safe * 100
    ).fillna(0)
    
    df_productos_precio['Margen_Unitario'] = (
        df_productos_precio['Precio_Actual'] - df_productos_precio['Costo_Promedio']
    )
    
    # Calcular rotación (participación en ventas)
    total_unidades = df_productos_precio['Unidades_Vendidas'].sum()
    df_productos_precio['Rotacion_Pct'] = (
        df_productos_precio['Unidades_Vendidas'] / total_unidades * 100
    ).fillna(0)
    
    # Ordenar por ventas
    df_productos_precio = df_productos_precio.sort_values('Venta_Total', ascending=False)
    
    # ========================================================================
    # SECCIÓN 1: ALERTAS DE MARGEN NEGATIVO 🚨
    # ========================================================================
    st.markdown("## 🚨 Alertas de Margen Negativo")
    
    df_margen_negativo = df_productos_precio[df_productos_precio['Margen_Pct'] < 0].copy()
    df_margen_negativo = df_margen_negativo.sort_values('Margen_Total', ascending=True)
    
    if not df_margen_negativo.empty:
        perdida_total = abs(df_margen_negativo['Margen_Total'].sum())
        
        st.error(f"⚠️ **{len(df_margen_negativo)} productos con margen NEGATIVO** - Pérdida estimada: **{format_currency(perdida_total)}**")
        
        with st.expander(f"🔴 Ver {len(df_margen_negativo)} productos con pérdida", expanded=True):
            
            # Top 10 con más pérdida
            st.markdown("#### 💸 Top 10 Productos con Mayor Pérdida")
            
            for idx, row in df_margen_negativo.head(10).iterrows():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{row['Descripcion'][:45]}**")
                with col2:
                    st.markdown(f"Costo: {format_currency(row['Costo_Promedio'])}")
                with col3:
                    st.markdown(f"Precio: {format_currency(row['Precio_Actual'])}")
                with col4:
                    st.markdown(f"🔴 Pérdida: {format_currency(abs(row['Margen_Total']))}")
            
            st.markdown("---")
            
            # Tabla completa de margen negativo
            st.markdown("#### 📋 Lista Completa")
            
            df_neg_display = df_margen_negativo[[
                'Codigo', 'Descripcion', 'Proveedor', 
                'Costo_Promedio', 'Precio_Actual', 'Margen_Pct',
                'Unidades_Vendidas', 'Margen_Total'
            ]].copy()
            
            df_neg_display['Precio_Sugerido'] = df_neg_display['Costo_Promedio'] * 1.15  # +15% margen mínimo
            precio_actual_safe = df_neg_display['Precio_Actual'].replace(0, pd.NA)
            df_neg_display['Aumento_Necesario'] = (
                (df_neg_display['Precio_Sugerido'] - df_neg_display['Precio_Actual']) / 
                precio_actual_safe * 100
            ).fillna(0)
            
            st.dataframe(
                df_neg_display.style.format({
                    'Costo_Promedio': '${:,.2f}',
                    'Precio_Actual': '${:,.2f}',
                    'Precio_Sugerido': '${:,.2f}',
                    'Margen_Pct': '{:.1f}%',
                    'Margen_Total': '${:,.2f}',
                    'Aumento_Necesario': '+{:.1f}%',
                    'Unidades_Vendidas': '{:,.0f}'
                }).applymap(
                    lambda x: 'background-color: #fee2e2' if isinstance(x, (int, float)) and x < 0 else '',
                    subset=['Margen_Pct', 'Margen_Total']
                ),
                use_container_width=True,
                height=300
            )
            
            # Exportar lista de margen negativo
            excel_negativos = to_excel(df_neg_display)
            st.download_button(
                label="📥 Exportar Productos con Margen Negativo",
                data=excel_negativos,
                file_name=f"margen_negativo_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.success("✅ ¡Excelente! No hay productos con margen negativo")
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 2: RESUMEN DE RENTABILIDAD ACTUAL
    # ========================================================================
    st.markdown("## 📊 Rentabilidad Actual")
    
    # Métricas globales
    venta_total_global = df_productos_precio['Venta_Total'].sum()
    costo_total_global = df_productos_precio['Costo_Total'].sum()
    margen_total_global = df_productos_precio['Margen_Total'].sum()
    margen_pct_global = (margen_total_global / costo_total_global * 100) if costo_total_global > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">VENTAS TOTALES</div>
            <div class="metric-value" style="color: #60a5fa;">{format_currency(venta_total_global)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">COSTO TOTAL</div>
            <div class="metric-value" style="color: #f97316;">{format_currency(costo_total_global)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">MARGEN TOTAL</div>
            <div class="metric-value" style="color: #10b981;">{format_currency(margen_total_global)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        color_margen = '#10b981' if margen_pct_global >= 20 else '#f97316' if margen_pct_global >= 10 else '#ef4444'
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">MARGEN %</div>
            <div class="metric-value" style="color: {color_margen};">{margen_pct_global:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 3: SIMULADOR DE PRICING
    # ========================================================================
    st.markdown("## 🎯 Simulador de Pricing")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Objetivo de Margen")
        
        margen_objetivo = st.slider(
            "¿Qué margen % querés alcanzar?",
            min_value=int(margen_pct_global),
            max_value=min(50, int(margen_pct_global) + 15),
            value=int(margen_pct_global) + 2,
            step=1,
            key="margen_objetivo_slider"
        )
        
        diferencia_margen = margen_objetivo - margen_pct_global
        
        st.markdown(f"""
        **Margen Actual:** {margen_pct_global:.1f}%  
        **Margen Objetivo:** {margen_objetivo}%  
        **Diferencia:** +{diferencia_margen:.1f}%
        """)
        
        # Estimar ganancia adicional
        ganancia_adicional_estimada = venta_total_global * (diferencia_margen / 100)
        st.success(f"💰 Ganancia adicional estimada: **{format_currency(ganancia_adicional_estimada)}**")
    
    with col2:
        st.markdown("### Estrategia de Aumento")
        
        estrategia = st.radio(
            "¿Cómo distribuir el aumento?",
            options=[
                "🎯 Inteligente (más a productos con bajo margen y alta rotación)",
                "📊 Uniforme (mismo % a todos los productos)",
                "🏭 Por Proveedor (seleccionar proveedores específicos)"
            ],
            key="estrategia_pricing"
        )
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 4: PRODUCTOS PROTEGIDOS (ANCLAS)
    # ========================================================================
    st.markdown("### 🔒 Productos Protegidos (Anclas de Precio)")
    st.info("Estos productos NO se modificarán porque son de referencia para los clientes")
    
    # Detectar automáticamente productos ancla (top ventas de categorías sensibles)
    palabras_ancla = ['leche', 'pan ', 'coca', 'pepsi', 'yerba', 'azucar', 'aceite', 'harina', 'arroz', 'fideos']
    
    # Sugerir productos ancla
    df_sugeridos_ancla = df_productos_precio[
        df_productos_precio['Descripcion'].str.lower().str.contains('|'.join(palabras_ancla), na=False)
    ].head(20)
    
    # Selector de productos protegidos
    productos_protegidos = st.multiselect(
        "Seleccionar productos a proteger",
        options=df_productos_precio['Descripcion'].tolist(),
        default=df_sugeridos_ancla['Descripcion'].tolist()[:10] if not df_sugeridos_ancla.empty else [],
        key="productos_protegidos"
    )
    
    st.markdown(f"**{len(productos_protegidos)} productos protegidos** (no se modificarán)")
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 5: SIMULACIÓN DE PRECIOS
    # ========================================================================
    st.markdown("## 📋 Simulación de Nuevos Precios")
    
    # Crear copia para simulación
    df_simulacion = df_productos_precio.copy()
    
    # Marcar protegidos
    df_simulacion['Protegido'] = df_simulacion['Descripcion'].isin(productos_protegidos)
    
    # Calcular aumento necesario por producto según estrategia
    def calcular_aumento(row, estrategia, diferencia_margen):
        """Calcula el % de aumento para cada producto"""
        
        # Evitar división por cero
        if row['Precio_Actual'] <= 0 or pd.isna(row['Precio_Actual']):
            return 0
        
        if row['Costo_Promedio'] <= 0 or pd.isna(row['Costo_Promedio']):
            return 0
        
        if row['Protegido']:
            return 0  # No tocar protegidos
        
        if row['Margen_Pct'] < 0:
            # Margen negativo: llevar a 15% mínimo sobre costo
            precio_minimo = row['Costo_Promedio'] * 1.15
            if row['Precio_Actual'] > 0:
                aumento = ((precio_minimo / row['Precio_Actual']) - 1) * 100
                return max(aumento, 0)
            else:
                return 0
        
        if "Inteligente" in estrategia:
            # Más aumento a productos con bajo margen y alta rotación
            factor_margen = max(0, (30 - row['Margen_Pct']) / 30)  # Más bajo el margen, más aumento
            factor_rotacion = min(row['Rotacion_Pct'] / 1, 1)  # Alta rotación aguanta más
            
            # Calcular aumento base
            aumento_base = diferencia_margen * 1.5  # Factor para compensar protegidos
            
            # Ajustar según factores
            aumento = aumento_base * (0.5 + factor_margen * 0.5) * (0.8 + factor_rotacion * 0.4)
            
            # Limitar: mínimo 0.5%, máximo 10%
            return max(0.5, min(10, aumento))
        
        elif "Uniforme" in estrategia:
            # Mismo % a todos (ajustado por protegidos)
            productos_no_protegidos = len(df_simulacion[~df_simulacion['Protegido']])
            factor_ajuste = len(df_simulacion) / productos_no_protegidos if productos_no_protegidos > 0 else 1
            return diferencia_margen * factor_ajuste
        
        else:
            return diferencia_margen
    
    # Aplicar cálculo
    df_simulacion['Aumento_Pct'] = df_simulacion.apply(
        lambda row: calcular_aumento(row, estrategia, diferencia_margen), 
        axis=1
    )
    
    # Calcular nuevos precios
    df_simulacion['Precio_Nuevo'] = df_simulacion['Precio_Actual'] * (1 + df_simulacion['Aumento_Pct'] / 100)
    
    # Calcular nuevo margen sobre COSTO
    costo_sim_safe = df_simulacion['Costo_Promedio'].replace(0, pd.NA)
    df_simulacion['Margen_Nuevo_Pct'] = (
        (df_simulacion['Precio_Nuevo'] - df_simulacion['Costo_Promedio']) / 
        costo_sim_safe * 100
    ).fillna(0)
    
    # Calcular impacto en ganancia
    df_simulacion['Margen_Nuevo_Total'] = (
        (df_simulacion['Precio_Nuevo'] - df_simulacion['Costo_Promedio']) * 
        df_simulacion['Unidades_Vendidas']
    )
    
    df_simulacion['Impacto_Ganancia'] = df_simulacion['Margen_Nuevo_Total'] - df_simulacion['Margen_Total']
    
    # Ordenar por impacto
    df_simulacion = df_simulacion.sort_values('Impacto_Ganancia', ascending=False)
    
    # ========================================================================
    # MOSTRAR RESULTADOS
    # ========================================================================
    
    # Métricas de la simulación
    margen_nuevo_total = df_simulacion['Margen_Nuevo_Total'].sum()
    margen_nuevo_pct = (margen_nuevo_total / costo_total_global * 100) if costo_total_global > 0 else 0
    ganancia_adicional_real = margen_nuevo_total - margen_total_global
    productos_afectados = len(df_simulacion[df_simulacion['Aumento_Pct'] > 0])
    aumento_promedio = df_simulacion[df_simulacion['Aumento_Pct'] > 0]['Aumento_Pct'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">PRODUCTOS AFECTADOS</div>
            <div class="metric-value">{productos_afectados}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">AUMENTO PROMEDIO</div>
            <div class="metric-value" style="color: #f97316;">+{aumento_promedio:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">NUEVO MARGEN</div>
            <div class="metric-value" style="color: #10b981;">{margen_nuevo_pct:.1f}%</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="card">
            <div class="metric-label">GANANCIA ADICIONAL</div>
            <div class="metric-value" style="color: #10b981;">{format_currency(ganancia_adicional_real)}</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs para ver resultados
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Precios", "📊 Análisis Visual", "🏭 Por Proveedor"])
    
    with tab1:
        st.markdown("### Lista de Precios Simulados")
        
        # Filtro rápido
        filtro_vista = st.radio(
            "Mostrar:",
            ["Todos", "Solo con aumento", "Solo protegidos", "Solo margen negativo"],
            horizontal=True,
            key="filtro_vista_precios"
        )
        
        df_mostrar = df_simulacion.copy()
        
        if filtro_vista == "Solo con aumento":
            df_mostrar = df_mostrar[df_mostrar['Aumento_Pct'] > 0]
        elif filtro_vista == "Solo protegidos":
            df_mostrar = df_mostrar[df_mostrar['Protegido'] == True]
        elif filtro_vista == "Solo margen negativo":
            df_mostrar = df_mostrar[df_mostrar['Margen_Pct'] < 0]
        
        # Preparar display
        df_display = df_mostrar[[
            'Codigo', 'Descripcion', 'Proveedor', 'Protegido',
            'Precio_Actual', 'Precio_Nuevo', 'Aumento_Pct',
            'Margen_Pct', 'Margen_Nuevo_Pct', 'Impacto_Ganancia'
        ]].head(200).copy()
        
        # Agregar indicadores visuales
        df_display['Estado'] = df_display.apply(
            lambda row: '🔒' if row['Protegido'] else ('🔴' if row['Margen_Pct'] < 0 else ('📈' if row['Aumento_Pct'] > 0 else '➖')),
            axis=1
        )
        
        # Formatear datos para mostrar limpio (precio unitario)
        df_display['Precio_Actual'] = df_display['Precio_Actual'].apply(format_currency)
        df_display['Precio_Nuevo'] = df_display['Precio_Nuevo'].apply(format_currency)
        df_display['Aumento_Pct'] = df_display['Aumento_Pct'].apply(lambda x: f"+{x:.1f}%" if x > 0 else "-")
        df_display['Margen_Pct'] = df_display['Margen_Pct'].apply(lambda x: f"{x:.1f}%")
        df_display['Margen_Nuevo_Pct'] = df_display['Margen_Nuevo_Pct'].apply(lambda x: f"{x:.1f}%")
        df_display['Impacto_Ganancia'] = df_display['Impacto_Ganancia'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(
            df_display[[
                'Estado', 'Codigo', 'Descripcion', 'Proveedor',
                'Precio_Actual', 'Precio_Nuevo', 'Aumento_Pct',
                'Margen_Pct', 'Margen_Nuevo_Pct', 'Impacto_Ganancia'
            ]].rename(columns={
                'Estado': '',
                'Precio_Actual': 'P.Actual',
                'Precio_Nuevo': 'P.Nuevo',
                'Aumento_Pct': 'Aumento',
                'Margen_Pct': 'Margen Actual',
                'Margen_Nuevo_Pct': 'Margen Nuevo',
                'Impacto_Ganancia': 'Impacto $'
            }),
            use_container_width=True,
            height=500,
            hide_index=True
        )
    
    with tab2:
        st.markdown("### Análisis Visual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribución de aumentos
            st.markdown("#### Distribución de Aumentos")
            
            df_no_protegido = df_simulacion[~df_simulacion['Protegido']]
            
            fig_dist = px.histogram(
                df_no_protegido,
                x='Aumento_Pct',
                nbins=20,
                title='Distribución de % de Aumento',
                labels={'Aumento_Pct': '% de Aumento', 'count': 'Cantidad de Productos'}
            )
            fig_dist.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            # Gráfico de margen antes vs después
            st.markdown("#### Margen: Antes vs Después")
            
            df_comparacion = pd.DataFrame({
                'Categoría': ['Margen Actual', 'Margen Simulado'],
                'Valor': [margen_pct_global, margen_nuevo_pct]
            })
            
            fig_comp = px.bar(
                df_comparacion,
                x='Categoría',
                y='Valor',
                color='Categoría',
                color_discrete_sequence=['#f97316', '#10b981'],
                title='Comparación de Margen %'
            )
            fig_comp.add_hline(y=margen_objetivo, line_dash="dash", line_color="red",
                             annotation_text=f"Objetivo: {margen_objetivo}%")
            fig_comp.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        
        # Gráfico de impacto por rango de margen
        st.markdown("#### Impacto por Rango de Margen Actual")
        
        df_simulacion['Rango_Margen'] = pd.cut(
            df_simulacion['Margen_Pct'],
            bins=[-100, 0, 10, 20, 30, 100],
            labels=['Negativo', '0-10%', '10-20%', '20-30%', '+30%']
        )
        
        df_por_rango = df_simulacion.groupby('Rango_Margen', observed=True).agg({
            'Impacto_Ganancia': 'sum',
            'Codigo': 'count',
            'Aumento_Pct': 'mean'
        }).reset_index()
        df_por_rango.columns = ['Rango', 'Impacto', 'Productos', 'Aumento_Prom']
        
        fig_rango = px.bar(
            df_por_rango,
            x='Rango',
            y='Impacto',
            color='Aumento_Prom',
            color_continuous_scale='RdYlGn',
            title='Impacto en Ganancia por Rango de Margen',
            labels={'Impacto': 'Impacto ($)', 'Aumento_Prom': 'Aumento Prom %'}
        )
        fig_rango.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_rango, use_container_width=True)
    
    with tab3:
        st.markdown("### Análisis por Proveedor")
        
        df_por_proveedor = df_simulacion.groupby('Proveedor', observed=True).agg({
            'Venta_Total': 'sum',
            'Margen_Total': 'sum',
            'Margen_Nuevo_Total': 'sum',
            'Impacto_Ganancia': 'sum',
            'Aumento_Pct': 'mean',
            'Codigo': 'count'
        }).reset_index()
        
        df_por_proveedor.columns = [
            'Proveedor', 'Ventas', 'Margen_Actual', 'Margen_Nuevo', 
            'Impacto', 'Aumento_Prom', 'Productos'
        ]
        
        df_por_proveedor['Margen_Pct_Actual'] = (df_por_proveedor['Margen_Actual'] / df_por_proveedor['Ventas'] * 100)
        df_por_proveedor['Margen_Pct_Nuevo'] = (df_por_proveedor['Margen_Nuevo'] / df_por_proveedor['Ventas'] * 100)
        
        df_por_proveedor = df_por_proveedor.sort_values('Impacto', ascending=False)
        
        st.dataframe(
            df_por_proveedor.head(30).rename(columns={
                'Ventas': 'Ventas $',
                'Margen_Actual': 'Margen $ Actual',
                'Margen_Nuevo': 'Margen $ Nuevo',
                'Impacto': 'Impacto $',
                'Aumento_Prom': 'Aumento Prom %',
                'Margen_Pct_Actual': 'Margen % Actual',
                'Margen_Pct_Nuevo': 'Margen % Nuevo'
            }),
            use_container_width=True,
            height=400,
            column_config={
                'Ventas $': st.column_config.NumberColumn(format="$%.0f"),
                'Margen $ Actual': st.column_config.NumberColumn(format="$%.0f"),
                'Margen $ Nuevo': st.column_config.NumberColumn(format="$%.0f"),
                'Impacto $': st.column_config.NumberColumn(format="$%.0f"),
                'Aumento Prom %': st.column_config.NumberColumn(format="%.1f%%"),
                'Margen % Actual': st.column_config.NumberColumn(format="%.1f%%"),
                'Margen % Nuevo': st.column_config.NumberColumn(format="%.1f%%"),
            }
        )
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 6: EXPORTAR
    # ========================================================================
    st.markdown("### 📥 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Lista de precios completa
        df_export_precios = df_simulacion[[
            'Codigo', 'Descripcion', 'Proveedor', 'Protegido',
            'Costo_Promedio', 'Precio_Actual', 'Precio_Nuevo', 'Aumento_Pct',
            'Margen_Pct', 'Margen_Nuevo_Pct', 'Unidades_Vendidas', 'Impacto_Ganancia'
        ]].copy()
        df_export_precios['Precio_Actual'] = pd.to_numeric(df_export_precios['Precio_Actual'], errors='coerce').round(2)
        df_export_precios['Precio_Nuevo'] = pd.to_numeric(df_export_precios['Precio_Nuevo'], errors='coerce').round(2)
        df_export_precios.columns = [
            'Codigo', 'Descripcion', 'Proveedor', 'Protegido',
            'Costo', 'Precio_Actual', 'Precio_Nuevo', 'Aumento_%',
            'Margen_Actual_%', 'Margen_Nuevo_%', 'Unidades', 'Impacto_$'
        ]
        
        excel_precios = to_excel(df_export_precios)
        st.download_button(
            label="📥 Lista de Precios Completa",
            data=excel_precios,
            file_name=f"simulacion_precios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # Solo productos con aumento
        df_solo_aumento = df_simulacion[df_simulacion['Aumento_Pct'] > 0][[
            'Codigo', 'Descripcion', 'Precio_Actual', 'Precio_Nuevo', 'Aumento_Pct'
        ]].copy()
        df_solo_aumento['Precio_Actual'] = pd.to_numeric(df_solo_aumento['Precio_Actual'], errors='coerce').round(2)
        df_solo_aumento['Precio_Nuevo'] = pd.to_numeric(df_solo_aumento['Precio_Nuevo'], errors='coerce').round(2)
        
        excel_aumento = to_excel(df_solo_aumento)
        st.download_button(
            label="📥 Solo Productos con Aumento",
            data=excel_aumento,
            file_name=f"productos_aumento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        # Resumen por proveedor
        excel_proveedor = to_excel(df_por_proveedor)
        st.download_button(
            label="📥 Resumen por Proveedor",
            data=excel_proveedor,
            file_name=f"resumen_proveedor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# ============================================================================
# FIN DEL MÓDULO SIMULADOR DE RENTABILIDAD
# ============================================================================

    # ============================================================================
    # REPORTES PERSONALIZADOS V2 (CON TODOS LOS MOVIMIENTOS)
    # ============================================================================
elif pagina == "📋 Reportes Personalizados":
    st.markdown('<h1 class="main-header">📋 Arma tus Propios Reportes</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Crea reportes personalizados con ventas, recepciones, transferencias y más</p>', unsafe_allow_html=True)

    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 1: TIPO DE DATOS
    # ========================================================================
    st.markdown("### 1️⃣ Tipo de Datos")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tipo_reporte = st.radio(
            "Fuente de datos",
            options=["Solo Ventas", "Todos los Movimientos"],
            help="Solo Ventas = df_filtrado | Todos = Ventas + Recepciones + Transferencias + Ajustes",
            key="tipo_reporte"
        )
    
    with col2:
        if tipo_reporte == "Todos los Movimientos":
            if df_todos_filtrado is None:
                st.warning("⚠️ No hay datos de movimientos completos disponibles")
                st.stop()
            
            tipos_movimiento_disponibles = df_todos_filtrado['Tipo_Movimiento'].unique().tolist()
            
            tipos_seleccionados = st.multiselect(
                "Tipos de movimiento a incluir",
                options=tipos_movimiento_disponibles,
                default=tipos_movimiento_disponibles,
                key="tipos_mov_reporte"
            )
            
            if not tipos_seleccionados:
                st.warning("⚠️ Seleccioná al menos un tipo de movimiento")
                st.stop()
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 2: COLUMNAS
    # ========================================================================
    st.markdown("### 2️⃣ Selecciona las Columnas")

    # Columnas base (comunes)
    columnas_base = {
        'Fecha': 'Fecha',
        'Tienda': 'Tienda',
        'Codigo': 'Código',
        'Descripcion': 'Descripción',
        'Proveedor': 'Proveedor',
        'Cantidad': 'Cantidad'
    }
    
    # Columnas adicionales según tipo
    if tipo_reporte == "Solo Ventas":
        columnas_disponibles = {
            **columnas_base,
            'Venta_Total': 'Ventas $',
            'Costo_Total': 'Costo $',
            'Margen': 'Margen $',
            'Margen_Pct': 'Margen %',
            'Precio_Venta': 'Precio Venta Unit.'
        }
        columnas_default = ['Fecha', 'Tienda', 'Codigo', 'Descripcion', 'Venta_Total', 'Margen']
    else:
        columnas_disponibles = {
            **columnas_base,
            'Tipo_Movimiento': 'Tipo de Movimiento',
            'Tienda_Origen': 'Tienda Origen',
            'Tienda_Destino': 'Tienda Destino',
            'Venta_Total': 'Ventas $',
            'Costo_Total': 'Costo $',
            'Costo': 'Costo Unitario',
            'Margen': 'Margen $',
            'Numero_Documento': 'Nro. Documento',
            'Precio_Venta': 'Precio Venta Unit.'
        }
        columnas_default = ['Fecha', 'Tipo_Movimiento', 'Tienda', 'Codigo', 'Descripcion', 'Cantidad']

    columnas_seleccionadas = st.multiselect(
        "Columnas a incluir en el reporte",
        options=list(columnas_disponibles.keys()),
        default=columnas_default,
        format_func=lambda x: columnas_disponibles[x],
        key="cols_reporte"
    )

    if not columnas_seleccionadas:
        st.warning("⚠️ Seleccioná al menos una columna")
        st.stop()

    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 3: FILTROS
    # ========================================================================
    st.markdown("### 3️⃣ Filtros Adicionales")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Determinar el dataframe a usar para los filtros
        df_source = df_todos_filtrado if tipo_reporte == "Todos los Movimientos" else df_filtrado
        
        proveedores_disponibles = sorted(df_source['Proveedor'].dropna().unique().tolist())
        proveedores_reporte = st.multiselect(
            "Filtrar por Proveedores (opcional)",
            options=proveedores_disponibles,
            default=[],
            key="proveedores_reporte"
        )

    with col2:
        tiendas_reporte = st.multiselect(
            "Filtrar por Tiendas (opcional)",
            options=todas_tiendas,
            default=[],
            key="tiendas_reporte"
        )
    
    with col3:
        busqueda_reporte = st.text_input(
            "Buscar Productos (opcional)",
            placeholder="Código o descripción...",
            key="buscar_reporte"
        )

    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 4: AGRUPACIÓN
    # ========================================================================
    st.markdown("### 4️⃣ ¿Agrupar Datos?")

    agrupar_datos = st.checkbox("Agrupar y sumarizar datos", value=False, key="agrupar_datos")

    if agrupar_datos:
        col1, col2 = st.columns(2)
        
        # Columnas que NO se pueden agrupar (son métricas)
        columnas_metricas = ['Cantidad', 'Venta_Total', 'Costo_Total', 'Margen', 'Margen_Pct', 'Precio_Venta', 'Costo']
        
        with col1:
            columnas_agrupar = st.multiselect(
                "Agrupar por",
                options=[c for c in columnas_seleccionadas if c not in columnas_metricas],
                default=['Tienda'] if 'Tienda' in columnas_seleccionadas else [],
                key="columnas_agrupar"
            )
        
        with col2:
            # Solo mostrar columnas métricas que estén seleccionadas
            metricas_disponibles = [c for c in columnas_metricas if c in columnas_seleccionadas]
            
            columnas_sumar = st.multiselect(
                "Sumar",
                options=metricas_disponibles,
                default=['Venta_Total'] if 'Venta_Total' in metricas_disponibles else (metricas_disponibles[:1] if metricas_disponibles else []),
                key="columnas_sumar"
            )

    st.markdown("---")

    # ========================================================================
    # BOTÓN GENERAR
    # ========================================================================
    if st.button("🚀 Generar Reporte", use_container_width=True, type="primary"):
        with st.spinner('Generando reporte...'):
            
            # ================================================================
            # PASO 1: SELECCIONAR FUENTE DE DATOS
            # ================================================================
            if tipo_reporte == "Solo Ventas":
                df_reporte = df_filtrado.copy()
            else:
                # Filtrar por tipos de movimiento seleccionados
                df_reporte = df_todos_filtrado[df_todos_filtrado['Tipo_Movimiento'].isin(tipos_seleccionados)].copy()
            
            # ================================================================
            # PASO 2: APLICAR FILTROS
            # ================================================================
            
            # Filtro de proveedores
            if len(proveedores_reporte) > 0:
                df_reporte = df_reporte[df_reporte['Proveedor'].isin(proveedores_reporte)]
            
            # Filtro de tiendas
            if len(tiendas_reporte) > 0:
                df_reporte = df_reporte[df_reporte['Tienda'].isin(tiendas_reporte)]
            
            # Filtro de búsqueda
            if busqueda_reporte:
                busqueda_lower = busqueda_reporte.lower()
                mask = (
                    df_reporte['Codigo'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                    df_reporte['Descripcion'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
                )
                df_reporte = df_reporte[mask]
            
            if df_reporte.empty:
                st.warning("⚠️ No hay datos que cumplan con los filtros seleccionados")
                st.stop()
            
            # ================================================================
            # PASO 3: AGRUPACIÓN (SI ESTÁ ACTIVADA)
            # ================================================================
            if agrupar_datos and len(columnas_agrupar) > 0 and len(columnas_sumar) > 0:
                # Crear diccionario de agregación
                agg_dict = {}
                for col in columnas_sumar:
                    if col in df_reporte.columns:
                        agg_dict[col] = 'sum'
                
                if agg_dict:
                    df_reporte = df_reporte.groupby(columnas_agrupar, observed=True).agg(agg_dict).reset_index()
                    
                    # Recalcular Margen % si está seleccionado
                    if 'Margen_Pct' in columnas_seleccionadas and 'Venta_Total' in df_reporte.columns and 'Margen' in df_reporte.columns:
                        df_reporte['Margen_Pct'] = (df_reporte['Margen'] / df_reporte['Venta_Total'] * 100).fillna(0)

            # ================================================================
            # PASO 4: SELECCIONAR COLUMNAS FINALES
            # ================================================================
            columnas_finales = [c for c in columnas_seleccionadas if c in df_reporte.columns]
            df_reporte_final = df_reporte[columnas_finales].copy()
            
            # Renombrar columnas a nombres amigables
            df_reporte_final.columns = [columnas_disponibles.get(c, c) for c in df_reporte_final.columns]
            
            # ================================================================
            # MOSTRAR RESULTADOS
            # ================================================================
            st.success(f"✅ Reporte generado: {len(df_reporte_final):,} registros")

            # Vista previa
            st.markdown("### 📊 Vista Previa del Reporte")
            st.dataframe(df_reporte_final.head(100), use_container_width=True, height=400)

            st.markdown("---")

            # ================================================================
            # EXPORTACIÓN
            # ================================================================
            col1, col2 = st.columns(2)
            
            with col1:
                excel_data = to_excel(df_reporte_final)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel_data,
                    file_name=f"reporte_yunta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                csv_data = df_reporte_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Descargar CSV",
                    data=csv_data,
                    file_name=f"reporte_yunta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            # ================================================================
            # ESTADÍSTICAS
            # ================================================================
            st.markdown("### 📊 Estadísticas del Reporte")
            
            # Contar columnas disponibles para métricas
            cols_metricas = []
            if 'Ventas $' in df_reporte_final.columns:
                cols_metricas.append(('Total Ventas', 'Ventas $', 'currency'))
            if 'Costo $' in df_reporte_final.columns:
                cols_metricas.append(('Total Costo', 'Costo $', 'currency'))
            if 'Margen $' in df_reporte_final.columns:
                cols_metricas.append(('Total Margen', 'Margen $', 'currency'))
            if 'Cantidad' in df_reporte_final.columns:
                cols_metricas.append(('Total Unidades', 'Cantidad', 'number'))
            
            # Agregar métrica de registros
            cols_metricas.insert(0, ('Total Registros', None, 'count'))
            
            # Crear columnas dinámicamente
            if len(cols_metricas) > 0:
                cols = st.columns(min(len(cols_metricas), 5))
                
                for idx, (label, col_name, tipo) in enumerate(cols_metricas):
                    with cols[idx % 5]:
                        if tipo == 'count':
                            st.metric(label, f"{len(df_reporte_final):,}")
                        elif tipo == 'currency':
                            st.metric(label, format_currency(df_reporte_final[col_name].sum()))
                        elif tipo == 'number':
                            st.metric(label, format_number(df_reporte_final[col_name].sum()))
            
            # ================================================================
            # ANÁLISIS ADICIONAL (si hay agrupación)
            # ================================================================
            if agrupar_datos and len(columnas_agrupar) > 0:
                st.markdown("---")
                st.markdown("### 📈 Análisis Visual")
                
                # Gráfico si hay datos numéricos
                if 'Ventas $' in df_reporte_final.columns and len(columnas_agrupar) == 1:
                    col_grupo = columnas_disponibles[columnas_agrupar[0]]
                    
                    # Top 10
                    df_top = df_reporte_final.nlargest(10, 'Ventas $')
                    
                    fig = px.bar(
                        df_top,
                        x=col_grupo,
                        y='Ventas $',
                        title=f"Top 10 por {col_grupo}",
                        color='Ventas $',
                        color_continuous_scale='blues'
                    )
                    fig.update_layout(
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
<div style='text-align:center; color:#64748b; padding:2rem 0; font-size:0.9rem;'>
    YUNTA Intelligence v2.3 - {datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(df_filtrado):,} registros de ventas cargados
</div>
""", unsafe_allow_html=True)