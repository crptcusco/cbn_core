import copy
import csv
import sys
import time
import json
from pathlib import Path
from tqdm import tqdm

# Configuración del path
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate

# --- PARÁMETROS ---
N_SAMPLES = 50 
N_LOCAL_NETWORKS_MIN = 5
N_LOCAL_NETWORKS_MAX = 8
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 10  # Topología aleatoria
NUM_CPUS = 4

output_dir = Path("outputs_benchmark_final")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_full_workflow_final.csv"

# Definición de los perfiles de ejecución
# (paso1, paso2, paso3, nombre_perfil)
PROFILES = [
    ("find_attractors_duvrova", "find_compatible_pairs", "mount_stable_attractor_fields", "seq"),
    ("find_local_attractors_parallel", "find_compatible_pairs_parallel", "mount_stable_attractor_fields_parallel", "par"),
    ("find_local_attractors_parallel_with_weights", "find_compatible_pairs_parallel_with_weights", "mount_stable_attractor_fields_parallel_chunks", "weights")
]

# Inicializar CSV
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample", "n_nets", "perfil", "t_p1", "t_p2", "t_p3", "total_t", "n_fields"])

template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
)

print(f"Iniciando Benchmark Final: {N_SAMPLES} samples | Topología: {V_TOPOLOGY}")

for i in tqdm(range(1, N_SAMPLES + 1), desc="Progreso Total"):
    for n_nets in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        
        for p1, p2, p3, name in PROFILES:
            # Crear directorio único para este perfil y sample
            iter_dir = output_dir / f"sample_{i}_nets_{n_nets}_{name}"
            iter_dir.mkdir(exist_ok=True)
            
            cbn = template.generate_cbn_from_template(v_topology=V_TOPOLOGY, n_local_networks=n_nets)
            
            # --- Ejecución y Cronometraje ---
            try:
                # Paso 1
                start = time.perf_counter()
                getattr(cbn, p1)()
                t_p1 = time.perf_counter() - start
                
                # Paso 2
                start = time.perf_counter()
                getattr(cbn, p2)()
                t_p2 = time.perf_counter() - start
                
                # Paso 3
                start = time.perf_counter()
                getattr(cbn, p3)()
                t_p3 = time.perf_counter() - start
                
                n_fields = len(cbn.d_attractor_fields)
                
                # Persistencia
                cbn.to_json(str(iter_dir / "topology.json"))
                with open(iter_dir / "dynamics_fields.json", "w") as f:
                    json.dump(cbn.to_json_fields(), f)
                
                # Registro CSV
                with open(csv_file, "a", newline="") as f:
                    csv.writer(f).writerow([i, n_nets, name, t_p1, t_p2, t_p3, t_p1+t_p2+t_p3, n_fields])
            
            except Exception as e:
                print(f"\n❌ Error en {name} | Sample {i} | Nets {n_nets}: {e}")
                continue

print(f"\nBenchmark finalizado. Resultados guardados en {csv_file}")