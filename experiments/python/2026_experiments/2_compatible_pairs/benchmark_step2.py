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

# --- PARÁMETROS DEL EXPERIMENTO ---
N_SAMPLES = 5 
N_LOCAL_NETWORKS_MIN = 8
N_LOCAL_NETWORKS_MAX = 12
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4
NUM_CPUS = 4

output_dir = Path("outputs_step2_advanced")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_compatible_pairs.csv"

def count_total_pairs(cbn):
    total = 0
    for net in cbn.l_local_networks:
        edges = cbn.find_output_edges_by_network_index(net.index, cbn.l_directed_edges)
        for edge in edges:
            total += len(edge.d_comp_pairs_attractors_by_value.get(0, []))
            total += len(edge.d_comp_pairs_attractors_by_value.get(1, []))
    return total

# Inicializar CSV
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample", "n_networks", "time_seq", "time_par", "pairs_seq", "pairs_par"])

template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
)

print(f"Iniciando Benchmark Step 2 (Duvrova + Parallel vs Sequential)")

for i in range(1, N_SAMPLES + 1):
    for n_nets in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        iter_dir = output_dir / f"sample_{i}_nets_{n_nets}"
        iter_dir.mkdir(exist_ok=True)
        
        base_cbn = template.generate_cbn_from_template(v_topology=V_TOPOLOGY, n_local_networks=n_nets)
        
        # 1. Usar Duvrova para atractores (más robusto ante variables)
        base_cbn.find_attractors_duvrova()
        
        # Guardar estado inicial
        base_cbn.to_json(str(iter_dir / "topology.json"))

        # Benchmark Secuencial
        cbn_seq = copy.deepcopy(base_cbn)
        start_seq = time.perf_counter()
        cbn_seq.find_compatible_pairs()
        time_seq = time.perf_counter() - start_seq
        pairs_seq = count_total_pairs(cbn_seq)

        # Benchmark Paralelo
        cbn_par = copy.deepcopy(base_cbn)
        start_par = time.perf_counter()
        cbn_par.find_compatible_pairs_parallel(num_cpus=NUM_CPUS)
        time_par = time.perf_counter() - start_par
        pairs_par = count_total_pairs(cbn_par)

        # 2. Validación de Integridad
        if pairs_seq != pairs_par:
            print(f"\n❌ ERROR DE INTEGRIDAD en sample {i}, redes {n_nets}")
            sys.exit(1)

        # Guardar dinámica
        # Guardar por separado para mayor limpieza
        with open(iter_dir / "dynamics_attractors.json", "w") as f:
            json.dump(cbn_seq.to_json_attractors(), f, indent=4)

        with open(iter_dir / "dynamics_pairs.json", "w") as f:
            json.dump(cbn_seq.to_json_pairs(), f, indent=4)

        # with open(iter_dir / "dynamics_fields.json", "w") as f:
        #     json.dump(cbn_final.to_json_fields(), f, indent=4)

        # Guardar resultados
        with open(csv_file, "a", newline="") as f:
            csv.writer(f).writerow([i, n_nets, f"{time_seq:.6f}", f"{time_par:.6f}", pairs_seq, pairs_par])

        print(f"Sample {i} | Networks: {n_nets} | OK")

print(f"Benchmark terminado. Resultados en: {csv_file}")

