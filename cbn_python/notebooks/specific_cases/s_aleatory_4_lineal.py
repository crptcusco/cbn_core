# import libraries
from cbnetwork.cbnetwork import CBN
from cbnetwork.utils.customtext import CustomText

# script to put a manual parameters for the example of 4 networks
print("LINEAL CBN ALEATORY SCRIPT EXAMPLE")
CustomText.print_duplex_line()

# pass the parameters
n_local_networks = 6
n_var_network = 5
n_output_variables = 2
n_clauses_function = 2
v_topology = 4  # path

o_cbn = CBN.generate_aleatory_cbn_by_topology(
    n_local_networks=n_local_networks,
    n_var_network=n_var_network,
    v_topology=v_topology,
    n_output_variables=n_output_variables,
)
# o_cbn.show_cbn_graph()

o_cbn.find_local_attractors_sequential()
# o_cbn.show_attractors()

o_cbn.find_compatible_pairs()
# o_cbn.show_attractor_pairs()

o_cbn.mount_stable_attractor_fields()
# o_cbn.show_attractors_fields()

# o_cbn.show_coupled_signals_kind()
