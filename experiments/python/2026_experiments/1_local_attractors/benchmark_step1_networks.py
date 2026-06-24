import copy
import csv
import sys
import time
import json
from pathlib import Path

# Configuración del path
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate
from cbnetwork.utils.customtext import CustomText

"""
Benchmark Avanzado: Estrategias con persistencia de JSON por cada iteración
"""

N_SAMPLES = 5 
N_LOCAL_NETWORKS_MIN = 8
N_LOCAL_NETWORKS_MAX = 12
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4

output_dir = Path("outputs_benchmark_networks")
output_dir.mkdir(exist_ok=True)
metrics_path = output_dir / "benchmark_consolidated.csv"

# Inicializar CSV
with open(metrics_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample", "n_networks", "time_bf", "count_bf", "time_par", "count_par", "time_par_w", "count_par_w", "time_sat", "count_sat"])

template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
)

def run_method(cbn, method_name):
    cbn_copy = copy.deepcopy(cbn)
    start = time.perf_counter()
    if method_name == "bf": cbn_copy.find_attractors_brute_force()
    elif method_name == "par": cbn_copy.find_local_attractors_parallel()
    elif method_name == "par_w": cbn_copy.find_local_attractors_parallel_with_weights()
    elif method_name == "sat": cbn_copy.find_attractors_duvrova()
    elapsed = time.perf_counter() - start
    return elapsed, cbn_copy.get_n_local_attractors(), cbn_copy

print("Iniciando Benchmark...")

for i in range(1, N_SAMPLES + 1):
    for n_nets in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        # Crear subcarpeta para esta iteración específica
        iter_dir = output_dir / f"sample_{i}_nets_{n_nets}"
        iter_dir.mkdir(exist_ok=True)
        
        base_cbn = template.generate_cbn_from_template(v_topology=V_TOPOLOGY, n_local_networks=n_nets)
        
        # Guardar topología original (antes de calcular atractores)
        base_cbn.to_json(str(iter_dir / "topology.json"))


        # Ejecución
        t_bf, c_bf, _ = run_method(base_cbn, "bf")
        t_par, c_par, _ = run_method(base_cbn, "par")
        t_par_w, c_par_w, _ = run_method(base_cbn, "par_w")
        t_sat, c_sat, cbn_final = run_method(base_cbn, "sat")

        # Guardar dinámica (estado final con atractores)
        with open(iter_dir / "dynamics.json", "w") as f:
            json.dump(cbn_final.to_json_attractors(), f, indent=4)

        # 1. Comprobación de Integridad
        results = [c_bf, c_par, c_par_w, c_sat]
        if not all(r == results[0] for r in results):
            print(f"\n❌ ERROR DE INTEGRIDAD en sample {i}, redes {n_nets}")
            sys.exit(1)

        # Guardar resultados
        with open(metrics_path, "a", newline="") as f:
            csv.writer(f).writerow([i, n_nets, f"{t_bf:.6f}", c_bf, f"{t_par:.6f}", c_par, f"{t_par_w:.6f}", c_par_w, f"{t_sat:.6f}", c_sat])

        print(f"Sample {i} | Nets: {n_nets} | JSONs guardados | OK")

print(f"Benchmark terminado con éxito.")