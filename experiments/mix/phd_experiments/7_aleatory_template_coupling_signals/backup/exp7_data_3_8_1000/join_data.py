import pandas as pd

# Leer los archivos CSV
csv1 = pd.read_csv("exp7_data_3_6_1000/data.csv")
csv2 = pd.read_csv("exp7_data_7_8_1000/data.csv")

# Unir los dos DataFrames
df_unido = pd.concat([csv1, csv2])

# Guardar el DataFrame unido en un nuevo archivo CSV
df_unido.to_csv("data.csv", index=False)

print("Los archivos CSV se han unido correctamente.")
