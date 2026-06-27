import copy
import csv
import sys
import time
import gc
from pathlib import Path
from tqdm import tqdm

# Configuración del path
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate

# --- PARÁMETROS ---
N_SAMPLES = 10
N_LOCAL_NETWORKS_MIN = 5
N_LOCAL_NETWORKS_MAX = 10
V_TOPOLOGY = 4

output_dir = Path("outputs_benchmark_granular")
output_dir.mkdir(exist_ok=True)
csv_file = output_dir / "benchmark_granular_workflow.csv"

# Definición de los 3 Perfiles
PROFILES = [
    ("find_attractors_duvrova", "find_compatible_pairs", "mount_stable_attractor_fields", "seq"),
    ("find_local_attractors_parallel", "find_compatible_pairs_parallel", "mount_stable_attractor_fields_parallel", "par"),
    ("find_local_attractors_parallel_with_weights", "find_compatible_pairs_parallel_with_weights", "mount_stable_attractor_fields_parallel_chunks", "weights")
]

# Inicializar CSV con las columnas solicitadas
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "sample", "n_nets", "perfil", 
        "t_p1", "t_p2", "t_p3", "total_t", 
        "n_attractors", "n_pairs", "n_fields"
    ])

template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=5, n_input_variables=2
)

print(f"Iniciando Benchmark Granular con Getters Nativos...")

for i in tqdm(range(1, N_SAMPLES + 1), desc="Progreso"):
    for n_nets in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        
        # 1. GENERAR RED BASE (Topología idéntica para todos los perfiles)
        base_cbn = template.generate_cbn_from_template(v_topology=V_TOPOLOGY, n_local_networks=n_nets)
        
        for p1, p2, p3, name in PROFILES:
            # 2. CLONAR RED (Estado limpio para cada perfil)
            cbn = copy.deepcopy(base_cbn)
            
            # --- MEDICIÓN GRANULAR ---
            start1 = time.perf_counter()
            getattr(cbn, p1)()
            t_p1 = time.perf_counter() - start1
            
            start2 = time.perf_counter()
            getattr(cbn, p2)()
            t_p2 = time.perf_counter() - start2
            
            start3 = time.perf_counter()
            getattr(cbn, p3)()
            t_p3 = time.perf_counter() - start3
            
            t_total = t_p1 + t_p2 + t_p3
            
            # --- EXTRACCIÓN DE MÉTRICAS (VÍA GETTERS NATIVOS) ---
            try:
                n_attractors = cbn.get_n_local_attractors()
            except Exception:
                n_attractors = 0
                
            try:
                n_pairs = cbn.get_n_pair_attractors()
            except Exception:
                n_pairs = 0
                
            try:
                n_fields = cbn.get_n_attractor_fields()
            except Exception:
                n_fields = 0
            
            # Registro en CSV
            with open(csv_file, "a", newline="") as f:
                csv.writer(f).writerow([
                    i, n_nets, name, 
                    f"{t_p1:.6f}", f"{t_p2:.6f}", f"{t_p3:.6f}", f"{t_total:.6f}",
                    n_attractors, n_pairs, n_fields
                ])
            
            # Limpieza del clon actual
            del cbn
            gc.collect()
            
        # Limpieza de la red base
        del base_cbn
        gc.collect()

print(f"\nBenchmark finalizado. Resultados en {csv_file}")