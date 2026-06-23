import copy
import csv
import sys
import time
from pathlib import Path

# Configuración del path
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate

"""
Experiment: Benchmark Exhaustivo - Crossover Analysis
Objetivo: Generar dataset para graficar la transición de eficiencia 
de Fuerza Bruta vs SAT (Duvrova) según el número de variables.
"""

# --- PARÁMETROS ---
N_SAMPLES = 1000
N_LOCAL_NETWORKS = 6
N_VAR_MIN = 10
N_VAR_MAX = 15
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4
# ------------------

# Crear carpeta de resultados
output_dir = Path("results_benchmark")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_crossover_data.csv"

print(
    f"Iniciando Benchmark: {N_VAR_MIN} a {N_VAR_MAX} variables | Redes: {N_LOCAL_NETWORKS}"
)
print("-" * 60)

# Escribir cabecera del CSV
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "sample_id",
            "n_variables",
            "n_local_networks",
            "attractors_bf",
            "attractors_sat",
            "match",
            "time_bf",
            "time_sat",
        ]
    )

for n_var in range(N_VAR_MIN, N_VAR_MAX + 1):
    print(f"Procesando redes con {n_var} variables...")

    for i in range(1, N_SAMPLES + 1):
        # Generar estructura de la red
        template = PathCircleTemplate.generate_path_circle_template(
            n_var_network=n_var, n_input_variables=N_INPUT_VARIABLES
        )
        cbn = template.generate_cbn_from_template(
            v_topology=V_TOPOLOGY, n_local_networks=N_LOCAL_NETWORKS
        )

        # 1. Ejecutar Fuerza Bruta
        cbn_bf = copy.deepcopy(cbn)
        start_bf = time.perf_counter()
        cbn_bf.find_attractors_brute_force()
        end_bf = time.perf_counter()

        time_bf = end_bf - start_bf
        count_bf = cbn_bf.get_n_local_attractors()

        # 2. Ejecutar Duvrova (SAT)
        cbn_sat = copy.deepcopy(cbn)
        start_sat = time.perf_counter()
        cbn_sat.find_attractors_duvrova()
        end_sat = time.perf_counter()

        time_sat = end_sat - start_sat
        count_sat = cbn_sat.get_n_local_attractors()

        is_match = count_bf == count_sat

        # Guardar en CSV
        with open(csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    i,
                    n_var,
                    N_LOCAL_NETWORKS,
                    count_bf,
                    count_sat,
                    is_match,
                    time_bf,
                    time_sat,
                ]
            )

print("-" * 60)
print(f"Benchmark terminado. Datos guardados en: {csv_file}")
