from pathlib import Path
import sys

# Agregar el directorio src al path para poder importar el paquete localmente
# Calcula la ruta del repositorio y añade `src` de forma robusta
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# internal imports
from cbnetwork.cbnetwork import CBN

# external imports

# Parameters
N_LOCAL_NETWORKS = 6
N_VARS_NETWORK = 5
V_TOPOLOGY = 4
N_EDGES = 10
N_INPUT_VARS = 2
N_OUTPUT_VARS = 2
N_MAX_CLAUSES = 2
N_MAX_LITERALS = 2

o_cbn = CBN.cbn_generator(
    v_topology=V_TOPOLOGY,
    n_local_networks=N_LOCAL_NETWORKS,
    n_vars_network=N_VARS_NETWORK,
    n_input_variables=N_INPUT_VARS,
    n_output_variables=N_OUTPUT_VARS,
    n_max_of_clauses=N_MAX_CLAUSES,
    n_max_of_literals=N_MAX_LITERALS,
    n_edges=N_EDGES,
)

o_cbn.show_resume()

# Find attractors
o_cbn.find_local_attractors_sequential()
o_cbn.show_local_attractors()

# find the compatible pairs
o_cbn.find_compatible_pairs()
o_cbn.show_attractor_pairs()

# Find attractor fields
o_cbn.mount_stable_attractor_fields()
o_cbn.show_stable_attractor_fields()

# show the kind of every coupled signal
o_cbn.show_coupled_signals_kind()

# Show the number of attractor fields by global scene
o_cbn.generate_global_scenes()
o_cbn.show_global_scenes()

# Count the attractor fields by global scene
o_cbn.count_fields_by_global_scenes()
