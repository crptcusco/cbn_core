import os
import shutil

# Definir las carpetas
carpeta1 = "pkl_cbn_1000"
carpeta2 = "pkl_cbn_270"
carpeta3 = "pkl_cbn_100"
carpeta_destino = "pkl_cbn"

# Crear la carpeta destino si no existe
os.makedirs(carpeta_destino, exist_ok=True)


def procesar_carpeta(
    carpeta_origen, digito_inicial, digito_incremento, limite, eliminar_corruptos
):
    if not os.path.isdir(carpeta_origen):
        print(f"Error: La carpeta '{carpeta_origen}' no existe.")
        return

    archivos = sorted([f for f in os.listdir(carpeta_origen) if f.endswith(".pkl")])

    if eliminar_corruptos and limite is not None:
        archivos = archivos[:limite]

    print(f"Procesando carpeta '{carpeta_origen}': {len(archivos)} archivos")

    for archivo in archivos:
        nuevo_digito = str(
            int(digito_inicial) + digito_incremento
        )  # Convertir a entero y luego a cadena
        nuevo_nombre = archivo.replace(f"cbn_{digito_inicial}_", f"cbn_{nuevo_digito}_")
        destino = os.path.join(carpeta_destino, nuevo_nombre)

        if not os.path.exists(destino):
            shutil.copy(os.path.join(carpeta_origen, archivo), destino)
        else:
            print(
                f"Advertencia: El archivo '{nuevo_nombre}' ya existe en la carpeta destino."
            )


# Procesar la primera carpeta (sin cambios en los nombres, solo eliminar corruptos)
procesar_carpeta(carpeta1, "1", 0, 6579, eliminar_corruptos=True)

# Procesar la segunda carpeta (actualizar el primer dígito a 2)
procesar_carpeta(carpeta2, "1", 1, 1619, eliminar_corruptos=True)

# Procesar la tercera carpeta (actualizar el primer dígito a 3)
procesar_carpeta(carpeta3, "1", 2, None, eliminar_corruptos=False)

# Filtrar para mantener solo los primeros 1012 muestras (1012 * 9 archivos)
archivos_destino = sorted(
    [f for f in os.listdir(carpeta_destino) if f.endswith(".pkl")]
)
archivos_a_conservar = archivos_destino[: 1012 * 9]

# Eliminar archivos adicionales
for archivo in archivos_destino:
    if archivo not in archivos_a_conservar:
        os.remove(os.path.join(carpeta_destino, archivo))

print(
    f"Total de archivos en la carpeta destino '{carpeta_destino}' después de ajuste: {len(os.listdir(carpeta_destino))}"
)
print("Archivos pickle combinados y renombrados correctamente en la carpeta 'pkl_cbn'.")
