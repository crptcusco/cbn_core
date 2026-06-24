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

# --- PARÁMETROS ---
N_SAMPLES = 50 
N_LOCAL_NETWORKS_MIN = 5
N_LOCAL_NETWORKS_MAX = 10
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4
NUM_CPUS = 4

output_dir = Path("outputs_step3_benchmark")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_full_workflow.csv"

# Inicializar CSV con columnas expandidas para cada método
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "sample", "n_nets", 
        "time_seq", "time_par", "time_chunks",
        "fields_seq", "fields_par", "fields_chunks"
    ])

template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
)

print(f"Iniciando Benchmark Completo (Paso 1, 2 y 3)")

for i in range(1, N_SAMPLES + 1):
    for n_nets in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        iter_dir = output_dir / f"sample_{i}_nets_{n_nets}"
        iter_dir.mkdir(exist_ok=True)
        
        # PASO 1: Duvrova
        cbn = template.generate_cbn_from_template(v_topology=V_TOPOLOGY, n_local_networks=n_nets)
        cbn.find_attractors_duvrova()
        
        # PASO 2: Pares compatibles
        cbn.find_compatible_pairs()
        
        # PASO 3: Benchmark de métodos de montaje
        def run_step3(cbn_in, method):
            c = copy.deepcopy(cbn_in)
            start = time.perf_counter()
            if method == "seq": c.mount_stable_attractor_fields()
            elif method == "par": c.mount_stable_attractor_fields_parallel()
            elif method == "chunks": c.mount_stable_attractor_fields_parallel_chunks()
            return time.perf_counter() - start, len(c.d_attractor_fields), c

        t3_seq, n_f1, cbn_s3 = run_step3(cbn, "seq")
        t3_par, n_f2, _ = run_step3(cbn, "par")
        t3_chunks, n_f3, _ = run_step3(cbn, "chunks")

        # Validación de integridad (debe ser estricta)
        if not (n_f1 == n_f2 == n_f3):
            print(f"\n❌ ERROR DE INTEGRIDAD en Paso 3: Seq={n_f1}, Par={n_f2}, Chunks={n_f3}")
            sys.exit(1)

        # Persistencia JSON
        cbn.to_json(str(iter_dir / "topology.json"))
        with open(iter_dir / "dynamics_attractors.json", "w") as f: json.dump(cbn.to_json_attractors(), f, indent=4)
        with open(iter_dir / "dynamics_pairs.json", "w") as f: json.dump(cbn.to_json_pairs(), f, indent=4)
        with open(iter_dir / "dynamics_fields.json", "w") as f: json.dump(cbn_s3.to_json_fields(), f, indent=4)

        # Registro CSV con métricas expandidas
        with open(csv_file, "a", newline="") as f:
            csv.writer(f).writerow([
                i, n_nets, 
                f"{t3_seq:.6f}", f"{t3_par:.6f}", f"{t3_chunks:.6f}",
                n_f1, n_f2, n_f3
            ])

        print(f"Sample {i} | Nets: {n_nets} | Fields: {n_f1} | OK")