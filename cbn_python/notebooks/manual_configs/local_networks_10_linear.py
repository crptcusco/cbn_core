# import libraries
import random

from cbnetwork.cbnetwork import CBN
from cbnetwork.directededge import DirectedEdge
from cbnetwork.internalvariable import InternalVariable
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.utils.customtext import CustomText

# script to put a manual parameters for the example of 4 networks
print("MESSAGE:", "LINEAL CBN MANUAL SCRIPT EXAMPLE")
print("==============================+++++++")

# pass the parameters
l_local_networks = []
l_directed_edges = []

n_local_nets = 10
n_var_net = 5
n_total_var = n_local_nets * n_var_net

# generate the 5 variables per network in sequence
d_network_variables = {
    i: list(range(n_var_net * (i - 1) + 1, n_var_net * i + 1))
    for i in range(1, n_local_nets + 1)
}

# generate the edges of the 1_linear_aleatory CBN
l_edges = [(i, i + 1) for i in range(1, 10)]

# generate the networks
for i_local_net in d_network_variables.keys():
    # generate the Local network
    o_local_network = LocalNetwork(i_local_net, d_network_variables[i_local_net])
    l_local_networks.append(o_local_network)
    # Show the local network
    o_local_network.show()

# generate the directed edges
cont_output_variable = 0
index_variable_signal = (n_local_nets * n_var_net) + 1
index_signal = 1
for t_edge in l_edges:
    l_output_variables = [4 + cont_output_variable, 5 + cont_output_variable]
    # generate coupling function
    coupling_function = " " + " ∧ ".join(map(str, l_output_variables)) + " "
    # generate the Directed Edge object
    o_directed_edge = DirectedEdge(
        index=index_signal,
        index_variable_signal=index_variable_signal,
        input_local_network=t_edge[1],
        output_local_network=t_edge[0],
        l_output_variables=l_output_variables,
        coupling_function=coupling_function,
    )
    # add the directed object to list
    l_directed_edges.append(o_directed_edge)
    # updating the count of variables
    cont_output_variable += 5
    # updating the index variable signal
    index_variable_signal += 1
    # update index signal
    index_signal += 1

# Generate the functions for every variable in the CBN
d_var_cnf_func = {}
count_network = 1
count_var = 0
for o_local_network in l_local_networks:
    d_var_cnf_func[count_var + 1] = [[count_var + 2, -(count_var + 3), count_var + 4]]
    d_var_cnf_func[count_var + 2] = [
        [count_var + 1, -(count_var + 3), -(count_var + 5)]
    ]
    d_var_cnf_func[count_var + 3] = [
        [-(count_var + 2), -(count_var + 4), count_var + 5]
    ]
    if o_local_network.index == 1:
        d_var_cnf_func[count_var + 4] = [[count_var + 3, count_var + 5]]
        d_var_cnf_func[count_var + 5] = [[count_var + 1, count_var + 2]]
    else:
        d_var_cnf_func[count_var + 4] = [
            [count_var + 3, count_var + 5, n_total_var + o_local_network.index - 1]
        ]
        d_var_cnf_func[count_var + 5] = [
            [-(count_var + 1), count_var + 2, n_total_var + o_local_network.index - 1]
        ]
    count_var += 5
    count_network += 1

# show the function for every variable
for key, value in d_var_cnf_func.items():
    print(key, "->", value)

# generating the local network dynamic
for o_local_network in l_local_networks:
    input_signals = CBN.find_input_edges_by_network_index(
        o_local_network.index, l_directed_edges
    )
    o_local_network.process_input_signals(input_signals)
    for i_local_variable in o_local_network.internal_variables:
        o_variable_model = InternalVariable(
            i_local_variable, d_var_cnf_func[i_local_variable]
        )
        o_local_network.descriptive_function_variables.append(o_variable_model)

# generating the CBN network
o_cbn = CBN(l_local_networks, l_directed_edges)

# Find attractors
o_cbn.find_local_attractors_sequential()

# show the kind of the edges
o_cbn.show_directed_edges()

# show the kind of every coupled signal
for o_directed_edge in o_cbn.l_directed_edges:
    print(
        "SIGNAL:",
        o_directed_edge.index_variable,
        "RELATION:",
        o_directed_edge.output_local_network,
        "->",
        o_directed_edge.input_local_network,
        "KIND:",
        o_directed_edge.kind_signal,
        "-",
        o_directed_edge.d_kind_signal[o_directed_edge.kind_signal],
    )

# show attractors
o_cbn.show_local_attractors()

# find the compatible pairs
o_cbn.find_compatible_pairs()
#
# show attractor pairs
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
CustomText.make_sub_title("Count Fields by global scenes")
print(o_cbn.count_fields_by_global_scenes())
