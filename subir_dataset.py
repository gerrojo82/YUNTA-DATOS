from datasets import Dataset
import pandas as pd

print("=== Subiendo datos a Hugging Face ===")
print("Usuario: gerrojo82")

# Rutas a tus archivos Parquet (ajusta si el path no es exacto)
ruta_cons = r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\pages\CONSOLIDADO_COMPLETO.parquet"
ruta_mov = r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\MOVIMIENTOS_STOCK_PowerBI.parquet"

print("\nCargando archivos...")
df_cons = pd.read_parquet(ruta_cons)
df_mov = pd.read_parquet(ruta_mov)

print(f"Consolidado: {df_cons.shape[0]:,} filas, {df_cons.shape[1]} columnas")
print(f"Movimientos: {df_mov.shape[0]:,} filas, {df_mov.shape[1]} columnas")

ds_cons = Dataset.from_pandas(df_cons)
ds_mov = Dataset.from_pandas(df_mov)

# Nombre exacto de tu dataset (copia de la URL que tenés abierta)
repo_id = "gerrojo82/yunta-dashboad-datos"

print(f"\nSubiendo a: {repo_id}")
print("Puede tardar 5–15 minutos según tamaño y conexión... NO CIERRES LA VENTANA")

ds_cons.push_to_hub(repo_id, config_name="consolidado", split="train")
ds_mov.push_to_hub(repo_id, config_name="movimientos", split="train")

print("\n¡Subida finalizada!")
print(f"Verifica en: https://huggingface.co/datasets/{repo_id}")
print("Ve a la pestaña 'Files and versions' para confirmar los archivos.")