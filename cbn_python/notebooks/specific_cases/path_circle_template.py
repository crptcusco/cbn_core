# local imports
from cbnetwork.localtemplates import PathCircleTemplate

# Experiment parameters
N_LOCAL_NETWORKS = 6
N_VAR_NETWORK = 5
N_OUTPUT_VARIABLES = 2
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4

# Generate the template for the experiment
o_path_circle_template = PathCircleTemplate.generate_path_circle_template(
    n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
)

# Generate the CBN with o template
o_cbn = o_path_circle_template.generate_cbn_from_template(
    v_topology=V_TOPOLOGY, n_local_networks=N_LOCAL_NETWORKS
)

# Show the CBN Information
o_cbn.show_description()

# Find Local attractors
o_cbn.find_local_attractors_sequential()
o_cbn.show_local_attractors()

# Find attractor pairs
o_cbn.find_compatible_pairs()
o_cbn.show_attractor_pairs()

# Find stable attractor fields
o_cbn.mount_stable_attractor_fields()
# o_cbn.show_stable_attractor_fields()
