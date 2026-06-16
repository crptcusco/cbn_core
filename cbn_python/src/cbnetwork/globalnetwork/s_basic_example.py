import logging

from globalnetwork import GlobalNetwork as gn

from classes.cbnetwork import CBN
from classes.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Script to test the Global Network class

# Parameters
N_LOCAL_NETWORKS = 6
N_VAR_NETWORK = 5
N_INPUT_VARIABLES = 2
N_OUTPUT_VARIABLES = 2
V_TOPOLOGY = 3

# Generate a Random CBN object
o_cbn = CBN.generate_aleatory_cbn_by_topology(
    n_local_networks=N_LOCAL_NETWORKS,
    n_var_network=N_VAR_NETWORK,
    v_topology=V_TOPOLOGY,
    n_output_variables=N_OUTPUT_VARIABLES,
    n_input_variables=N_INPUT_VARIABLES,
)
o_cbn.show_description()

# Find the global stable states
o_cbn.find_local_attractors_sequential()
o_cbn.find_compatible_pairs()
o_cbn.mount_stable_attractor_fields()
# o_cbn.show_stable_attractor_fields()

# Generate Global Network
o_gn = gn.generate_global_network(o_cbn)

# transform the local attractor fields to global stable states
l_global_stable_state = gn.transform_attractor_fields_to_global_states(
    o_cbn.d_attractor_fields
)

l_global_stable_states = []
for o_attractor_field in o_cbn.d_attractor_fields:
    stable_state_index_attractors = []
    for t_pair in o_attractor_field:
        stable_state_index_attractors.append(t_pair[0].l_index)
        stable_state_index_attractors.append(t_pair[1].l_index)
    logger.info("%s", stable_state_index_attractors)

# # Test the stable attractor fields
# CBN.test_attractor_fields(o_cbn)

# # generate the global scenes
# o_cbn.generate_global_scenes()
# o_cbn.show_global_scenes()

# # generate a global transition
# # generate a global state
# # generate a global state aleatorio or manual
