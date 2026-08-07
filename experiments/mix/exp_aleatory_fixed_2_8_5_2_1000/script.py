import pandas as pd

# 1. Cargar el archivo con los datos combinados
# (Asegúrate de poner el nombre exacto de tu archivo de salida)
file_path = "benchmark_granular_workflow.csv" 
df = pd.read_csv(file_path)

# Asumimos que la primera columna es 'sample_id'. Si tiene otro nombre, cámbialo aquí.
col_id = df.columns[0] 

# 2. Detectar dónde ocurre la caída (ej. de 815 baja a 1)
# diff() resta la fila actual menos la anterior. Una caída negativa fuerte indica el reinicio.
restart_indices = df[df[col_id].diff() < 0].index

if not restart_indices.empty:
    restart_idx = restart_indices[0]
    
    last_correct_id = df.loc[restart_idx - 1, col_id]
    restarted_id = df.loc[restart_idx, col_id]
    
    print(f"🚨 Reinicio detectado en el índice {restart_idx}.")
    print(f"Último ID correcto: {last_correct_id} | El ID reinició en: {restarted_id}")
    
    # 3. Calcular el desfase (offset) exacto
    # Si terminó en 815 y reinició en 1, el offset es 815
    offset = last_correct_id - (restarted_id - 1)
    
    # 4. Aplicar la suma a todo el bloque nuevo
    df.loc[restart_idx:, col_id] += offset
    
    # 5. Guardar el resultado limpio en un nuevo archivo
    fixed_file = "benchmark_granular_workflow_fixed.csv"
    df.to_csv(fixed_file, index=False)
    
    print(f"✅ ¡Numeración corregida! Archivo guardado como: {fixed_file}")
    print(f"Muestra inicial del nuevo bloque ajustada de {restarted_id} a {df.loc[restart_idx, col_id]}")
else:
    print("No se detectó ningún salto negativo en la numeración. El archivo parece continuo.")