# internal imports
from cbnetwork.cbnetwork import CBN
from cbnetwork.directededge import DirectedEdge
from cbnetwork.internalvariable import InternalVariable
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.utils.customtext import CustomText

# script to put a manual parameters for the example of 4 networks
CustomText.print_duplex_line()
print("CBN MANUAL SCRIPT EXAMPLE: 4 NETWORKS")

# pass the CBN properties
l_local_networks = []
l_directed_edges = []
l_index_local_networks = list(range(1, 5))
d_network_variables = {
    1: [1, 2, 3],
    2: [4, 5, 6, 7],
    3: [8, 9, 10],
    4: [11, 12, 13, 14],
}

l_edges = [(2, 1), (3, 2), (2, 3), (4, 3)]

# generate the networks
CustomText.print_duplex_line()
print("Creating the local networks")
for i_local_net in d_network_variables.keys():
    o_local_network = LocalNetwork(i_local_net, d_network_variables[i_local_net])
    print("Local Network", i_local_net, "created.")
    l_local_networks.append(o_local_network)

# generate the directed edges
l_directed_edges.append(DirectedEdge(1, 15, 1, 2, [4, 5], " 4 ∧ 5 "))
l_directed_edges.append(DirectedEdge(2, 16, 2, 3, [8, 9], " 8 ∨ 9 "))
l_directed_edges.append(DirectedEdge(3, 17, 3, 2, [6, 7], " 6 ∧ 7 "))
l_directed_edges.append(DirectedEdge(4, 18, 3, 4, [13, 14], " 13 ∨ 14 "))

# variables functions in CNF format
d_variable_cnf_function = {
    1: [[2, 3], [1, -15]],
    2: [[1, 15]],
    3: [[3, -1, 15]],
    4: [[-5, 6, 7]],
    5: [[6, -7, -16]],
    6: [[-4, -5, 16]],
    7: [[-5, 16, 7]],
    8: [[9, 10, 17]],
    9: [[8, 18]],
    10: [[8, 9]],
    11: [[-12, 13]],
    12: [[11, 13]],
    13: [[14, -11, 12]],
    14: [[11, -12]],
}

# generating the local network dynamic
CustomText.print_duplex_line()
print("Generating the dynamics of the local networks")
for o_local_network in l_local_networks:
    input_signals = CBN.find_input_edges_by_network_index(
        o_local_network.index, l_directed_edges
    )
    # add the input variables to the local network object
    o_local_network.process_input_signals(input_signals)
    for i_local_variable in o_local_network.internal_variables:
        o_variable_model = InternalVariable(
            i_local_variable, d_variable_cnf_function[i_local_variable]
        )
        o_local_network.descriptive_function_variables.append(o_variable_model)

# generating the CBN network
CustomText.print_duplex_line()
print("Creating the Coupled Boolean Network object...")
o_cbn = CBN(l_local_networks, l_directed_edges)
print("CBN object created")

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
CustomText.make_sub_title("Count Fields by global scenes")
print(o_cbn.count_fields_by_global_scenes())
