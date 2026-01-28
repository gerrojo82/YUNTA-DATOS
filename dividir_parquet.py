import pandas as pd

# Cargar el archivo grande
print("Cargando archivo...")
df = pd.read_parquet(r"C:\Users\German\DASHBOARDYUNTA\YUNTA DASHBOARD INTELIGENTE\MOVIMIENTOS_STOCK_PowerBI.parquet")

print(f"Total filas: {len(df):,}")
print(f"Columnas: {list(df.columns)}")

# Partir en 3 archivos
n_partes = 3
filas_por_parte = len(df) // n_partes

for i in range(n_partes):
    inicio = i * filas_por_parte
    fin = (i + 1) * filas_por_parte if i < n_partes - 1 else len(df)
    
    df_parte = df.iloc[inicio:fin]
    nombre = f"MOVIMIENTOS_PARTE_{i+1}.parquet"
    df_parte.to_parquet(nombre, index=False)
    print(f"✅ {nombre}: {len(df_parte):,} filas guardadas")

print("\n🎉 Listo! Ahora subí los 3 archivos a Google Drive")