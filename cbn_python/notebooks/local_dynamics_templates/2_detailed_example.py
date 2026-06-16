# internal imports
from cbnetwork.cbnetwork import CBN
from cbnetwork.globaltopology import GlobalTopology
from cbnetwork.localtemplates import LocalNetworkTemplate

# external imports

# Parameters
N_LOCAL_NETWORKS = 6
N_VARS_NETWORK = 5
V_TOPOLOGY = 2
N_EDGES = 6
N_INPUT_VARS = 2
N_OUTPUT_VARS = 2
N_MAX_CLAUSES = 2
N_MAX_LITERALS = 2

# GENERATE THE GLOBAL TOPOLOGY
o_global_topology = GlobalTopology.generate_sample_topology(
    v_topology=V_TOPOLOGY, n_nodes=N_LOCAL_NETWORKS, n_edges=N_EDGES
)

# Ensure topology was created (helps static checkers know this isn't None)
assert o_global_topology is not None, "Failed to generate global topology"

# GENERATE THE LOCAL NETWORK TEMPLATE
o_template = LocalNetworkTemplate(
    n_vars_network=N_VARS_NETWORK,
    n_input_variables=N_INPUT_VARS,
    n_output_variables=N_OUTPUT_VARS,
    n_max_of_clauses=N_MAX_CLAUSES,
    n_max_of_literals=N_MAX_LITERALS,
    v_topology=V_TOPOLOGY,
)

# GENERATE THE CBN WITH THE TOPOLOGY AND TEMPLATE
o_cbn = CBN.generate_cbn_from_template(
    v_topology=V_TOPOLOGY,
    n_local_networks=N_LOCAL_NETWORKS,
    n_vars_network=N_VARS_NETWORK,
    o_template=o_template,
    l_global_edges=o_global_topology.l_edges,
)

o_cbn.show_description()

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
print(o_cbn.count_fields_by_global_scenes())
