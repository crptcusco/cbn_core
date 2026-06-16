import pandas as pd

# Cargar los archivos CSV y seleccionar los datos válidos
df1 = pd.read_csv("data_1000.csv").iloc[
    : 731 * 9
]  # Consideramos que cada sample tiene 9 registros
df2 = pd.read_csv("data_270.csv").iloc[: 179 * 9]  # Hacemos lo mismo aquí
df3 = pd.read_csv("data_100.csv")  # Este archivo está completo

# Ajustar el índice 'i_sample' en cada DataFrame
df2["i_sample"] += 731
df3["i_sample"] += 731 + 179

# Combinar los tres DataFrames en uno solo
df_combined = pd.concat([df1, df2, df3], ignore_index=True)

# Verificar cuántos samples únicos hay en el DataFrame combinado
num_samples = df_combined["i_sample"].nunique()
total_registros = len(df_combined)

print(f"Total de samples únicos en el DataFrame combinado: {num_samples}")
print(f"Total de registros en el DataFrame combinado: {total_registros}")

# Identificar las muestras únicas y eliminarlas desde el final para quedarnos con 1000
unique_samples = df_combined["i_sample"].unique()  # Obtener muestras únicas
samples_to_keep = unique_samples[:-10]  # Mantener todas menos las últimas 12

# Filtrar el DataFrame para quedarse solo con las muestras deseadas
df_filtered = df_combined[df_combined["i_sample"].isin(samples_to_keep)]

# Guardar el DataFrame filtrado en un nuevo archivo CSV
df_filtered.to_csv("data.csv", index=False)

print("Los últimos 10 samples han sido eliminados. Archivo guardado como 'data.csv'.")
