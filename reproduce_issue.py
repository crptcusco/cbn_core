import sys
from pathlib import Path

# Configuración del path
root_dir = Path(__file__).resolve().parents[0]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate
from cbnetwork.cbnetwork import CBN

def test_repro():
    template = PathCircleTemplate.generate_path_circle_template(
        n_var_network=3, n_input_variables=1
    )
    
    n_nets = 3
    v_topology = 4 # Path
    
    print(f"Generando red con {n_nets} redes locales, topología {v_topology}...")
    cbn = template.generate_cbn_from_template(v_topology=v_topology, n_local_networks=n_nets)
    
    print("Paso 1: Buscando atractores locales (Duvrova)...")
    cbn.find_attractors_duvrova()
    n_attractors = cbn.get_n_local_attractors()
    print(f"Atractores locales encontrados: {n_attractors}")
    
    print("Paso 2: Buscando pares compatibles...")
    cbn.find_compatible_pairs()
    n_pairs = cbn.get_n_pair_attractors()
    print(f"Pares compatibles encontrados: {n_pairs}")
    
    for edge in cbn.l_directed_edges:
        print(f"Edge {edge.index}: {edge.output_local_network} -> {edge.input_local_network}")
        print(f"  Atractores salida value 0: {[a.g_index for a in edge.d_out_value_to_attractor[0]]}")
        print(f"  Atractores salida value 1: {[a.g_index for a in edge.d_out_value_to_attractor[1]]}")
        print(f"  Pares compatibles value 0: {edge.d_comp_pairs_attractors_by_value[0]}")
        print(f"  Pares compatibles value 1: {edge.d_comp_pairs_attractors_by_value[1]}")
    
    print("Paso 3: Montando campos de atractores estables...")
    cbn.mount_stable_attractor_fields()
    n_fields = cbn.get_n_attractor_fields()
    print(f"Campos de atractores (Attractor Fields) encontrados: {n_fields}")

if __name__ == "__main__":
    test_repro()
