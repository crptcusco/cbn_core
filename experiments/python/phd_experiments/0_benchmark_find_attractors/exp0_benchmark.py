import copy
import json
import sys
import time
from pathlib import Path

# Add project root to sys.path to allow importing from cbn_python/src
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate
from cbnetwork.utils.customtext import CustomText

"""
Experiment 0 - BENCHMARK: Brute Force vs Duvrova (SAT)
Objetivo: Medir tiempos de ejecución y validar que ambos métodos 
encuentran los mismos resultados en topologías idénticas.
"""

# experiment parameters
N_SAMPLES = 10
N_LOCAL_NETWORKS_MIN = 3
N_LOCAL_NETWORKS_MAX = 11
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4

# Begin the Experiment
print("BEGIN THE BENCHMARK EXPERIMENT")
print("=" * 80)

v_begin_exp = time.time()
EXPERIMENT_NAME = "exp0_benchmark_bf_vs_sat"

OUTPUT_FOLDER = Path("outputs")
OUTPUT_FOLDER.mkdir(exist_ok=True)

DIRECTORY_PATH = (
    OUTPUT_FOLDER
    / f"{EXPERIMENT_NAME}_{N_LOCAL_NETWORKS_MIN}_{N_LOCAL_NETWORKS_MAX}_{N_SAMPLES}"
)
DIRECTORY_PATH.mkdir(exist_ok=True)

metrics_path = DIRECTORY_PATH / "benchmark_metrics.csv"

# Modificamos el header para enfocarnos en la carrera entre ambos algoritmos
if not metrics_path.exists():
    with metrics_path.open("w") as f:
        f.write(
            "i_sample,n_local_networks,n_var_network,v_topology,"
            "n_attractors_bf,n_attractors_sat,is_match,"
            "time_brute_force,time_duvrova\n"
        )

for i_sample in range(1, N_SAMPLES + 1):
    o_path_circle_template = PathCircleTemplate.generate_path_circle_template(
        n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
    )

    for n_local_networks in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        print(
            f"Benchmark {i_sample}/{N_SAMPLES} | Networks: {n_local_networks} | TOPOLOGY: {V_TOPOLOGY}"
        )

        # Generamos la red base (Oráculo)
        o_cbn_base = o_path_circle_template.generate_cbn_from_template(
            v_topology=V_TOPOLOGY, n_local_networks=n_local_networks
        )

        # ---------------------------------------------------------
        # COMPETIDOR 1: FUERZA BRUTA
        # ---------------------------------------------------------
        o_cbn_bf = copy.deepcopy(o_cbn_base)
        v_begin_bf = time.time()
        o_cbn_bf.find_attractors_brute_force()
        v_end_bf = time.time()

        time_bf = v_end_bf - v_begin_bf
        attractors_bf = o_cbn_bf.get_n_local_attractors()

        # ---------------------------------------------------------
        # COMPETIDOR 2: DUVROVA (SAT)
        # ---------------------------------------------------------
        o_cbn_sat = copy.deepcopy(o_cbn_base)
        v_begin_sat = time.time()
        o_cbn_sat.find_attractors_duvrova()
        v_end_sat = time.time()

        time_sat = v_end_sat - v_begin_sat
        attractors_sat = o_cbn_sat.get_n_local_attractors()

        # ---------------------------------------------------------
        # VALIDACIÓN Y LOGS
        # ---------------------------------------------------------
        # La prueba de fuego: ¿Ambos algoritmos encontraron lo mismo?
        is_match = attractors_bf == attractors_sat

        with metrics_path.open("a") as f:
            metrics = [
                i_sample,
                n_local_networks,
                N_VAR_NETWORK,
                V_TOPOLOGY,
                attractors_bf,
                attractors_sat,
                is_match,
                time_bf,
                time_sat,
            ]
            f.write(",".join(map(str, metrics)) + "\n")

        # Imprimir resultados en consola para ver la carrera en vivo
        print(f"  -> Fuerza Bruta: {time_bf:.4f}s ({attractors_bf} atractores)")
        print(f"  -> Duvrova (SAT): {time_sat:.4f}s ({attractors_sat} atractores)")
        print(f"  -> Match de resultados: {'✅ SÍ' if is_match else '❌ NO'}")

        CustomText.print_duplex_line()

v_end_exp = time.time()
print(f"Time experiment (in seconds): {v_end_exp - v_begin_exp:.2f}")
print("=" * 80)
print("END BENCHMARK EXPERIMENT")
