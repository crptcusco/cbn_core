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

"""
Benchmark Exhaustivo: Crossover Analysis con todos los métodos.
Objetivo: Medir BF, SAT, Paralelo y Paralelo Ponderado variando n_variables.
"""

N_SAMPLES = 5
N_LOCAL_NETWORKS = 6
N_VAR_MIN = 10
N_VAR_MAX = 12
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4

output_dir = Path("results_benchmark_variables")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_crossover_data.csv"

# Función unificada para todos los métodos
def run_method(cbn, method_name):
    cbn_copy = copy.deepcopy(cbn)
    start = time.perf_counter()
    if method_name == "bf": cbn_copy.find_attractors_brute_force()
    elif method_name == "par": cbn_copy.find_local_attractors_parallel()
    elif method_name == "par_w": cbn_copy.find_local_attractors_parallel_with_weights()
    elif method_name == "sat": cbn_copy.find_attractors_duvrova()
    elapsed = time.perf_counter() - start
    return elapsed, cbn_copy.get_n_local_attractors(), cbn_copy

# Inicializar CSV
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "sample", "n_vars", "time_bf", "count_bf", 
        "time_par", "count_par", "time_par_w", "count_par_w", 
        "time_sat", "count_sat"
    ])

print(f"Iniciando Benchmark: {N_VAR_MIN} a {N_VAR_MAX} variables")

for n_var in range(N_VAR_MIN, N_VAR_MAX + 1):
    for i in range(1, N_SAMPLES + 1):
        iter_dir = output_dir / f"nvar_{n_var}_sample_{i}"
        iter_dir.mkdir(exist_ok=True)

        template = PathCircleTemplate.generate_path_circle_template(
            n_var_network=n_var, n_input_variables=N_INPUT_VARIABLES
        )
        base_cbn = template.generate_cbn_from_template(
            v_topology=V_TOPOLOGY, n_local_networks=N_LOCAL_NETWORKS
        )
        base_cbn.to_json(str(iter_dir / "topology.json"))

        # Ejecución de todos los métodos
        t_bf, c_bf, _ = run_method(base_cbn, "bf")
        t_par, c_par, _ = run_method(base_cbn, "par")
        t_par_w, c_par_w, _ = run_method(base_cbn, "par_w")
        t_sat, c_sat, cbn_final = run_method(base_cbn, "sat")

        # Validación de Integridad
        results = [c_bf, c_par, c_par_w, c_sat]
        if not all(r == results[0] for r in results):
            print(f"\n❌ ERROR DE INTEGRIDAD en n_var {n_var}, sample {i}")
            sys.exit(1)

        # Persistencia dinámica
        with open(iter_dir / "dynamics.json", "w") as f:
            json.dump(cbn_final.to_json_attractors(), f, indent=4)

        # Registro CSV
        with open(csv_file, "a", newline="") as f:
            csv.writer(f).writerow([
                i, n_var, f"{t_bf:.6f}", c_bf, f"{t_par:.6f}", c_par, 
                f"{t_par_w:.6f}", c_par_w, f"{t_sat:.6f}", c_sat
            ])

        print(f"Var {n_var} | Sample {i} | OK")

print(f"Benchmark terminado. Datos en: {csv_file}")