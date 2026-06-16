# local imports
from cbnetwork.cbnetwork import CBN
from cbnetwork.utils.customtext import CustomText

CustomText.make_principal_title("SCRIPT TO TEST ALL THE FUNCTIONALITIES")

# pass the parameters
N_LOCAL_NETWORKS = 4
N_EDGES = 4
N_VAR_NETWORK = 5
N_OUTPUT_VARIABLES = 2
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 1
N_MAX_CLAUSES = 2
N_MAX_LITERALS = 2

# generate aleatory CBN by topology
# o_cbn = CBN.generate_aleatory_cbn_by_topology(n_local_networks=N_LOCAL_NETWORKS, n_var_network=N_VAR_NETWORK,
#                                               v_topology=V_TOPOLOGY, n_output_variables=N_OUTPUT_VARIABLES)

o_cbn = CBN.cbn_generator(
    v_topology=V_TOPOLOGY,
    n_edges=N_EDGES,
    n_vars_network=N_VAR_NETWORK,
    n_local_networks=N_LOCAL_NETWORKS,
    n_input_variables=N_INPUT_VARIABLES,
    n_output_variables=N_OUTPUT_VARIABLES,
    n_max_of_clauses=N_MAX_CLAUSES,
    n_max_of_literals=N_MAX_LITERALS,
)

o_cbn.find_local_attractors_sequential()
o_cbn.find_compatible_pairs()
o_cbn.mount_stable_attractor_fields()

# Testing methods
o_cbn.show_local_attractors()
o_cbn.show_local_attractors_dictionary()
o_cbn.show_attractor_pairs()
o_cbn.show_attractors_fields()
o_cbn.show_stable_attractor_fields_detailed()
o_cbn.show_coupled_signals_kind()
o_cbn.show_resume()

# show the kind of every coupled signal
o_cbn.show_coupled_signals_kind()

# Show the number of attractor fields by global scene
o_cbn.generate_global_scenes()
o_cbn.show_global_scenes()

# Count the attractor fields by global scene
print(o_cbn.count_fields_by_global_scenes())
