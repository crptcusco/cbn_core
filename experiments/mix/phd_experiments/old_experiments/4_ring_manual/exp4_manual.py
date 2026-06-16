# external imports
import time

import pandas as pd

# local imports
from classes.cbnetwork import CBN
from classes.directededge import DirectedEdge
from classes.internalvariable import InternalVariable
from classes.localnetwork import LocalNetwork
from classes.utils.customtext import CustomText

"""
Experiment 1 - Test the 3_ring_aleatory structure 
using aleatory generated networks
number of local networks 3  
"""

# experiment parameters
n_samples = 1
n_local_networks_min = 3
n_local_networks_max = 10
n_var_network = 5
n_output_variables = 2
v_topology = 3  # cycle graph
n_clauses_function = 2

# Begin Experiment

# Capture the time for all the experiment
v_begin_exp = time.time()

# Begin the process
l_data_sample = []
for n_local_networks in range(n_local_networks_min, n_local_networks_max):
    for i_sample in range(1, n_samples + 1):
        print("Experiment", i_sample, "of", n_samples)

        l_local_networks = []
        l_directed_edges = []

        n_local_nets = n_local_networks
        n_var_net = n_var_network
        n_total_var = n_local_nets * n_var_net

        # generate the 5 variables per network in sequence
        d_network_variables = {
            i: list(range(n_var_net * (i - 1) + 1, n_var_net * i + 1))
            for i in range(1, n_local_nets + 1)
        }

        # generate the edges of the 1_linear_aleatory CBN
        l_edges = [(i, i + 1) for i in range(1, n_local_networks)]

        # generate the networks
        for i_local_net in d_network_variables.keys():
            # generate the Local network
            o_local_network = LocalNetwork(
                i_local_net, d_network_variables[i_local_net]
            )
            l_local_networks.append(o_local_network)
            # Show the local network
            o_local_network.show()

        # create the directed edges
        cont_output_variable = 0
        index_variable_signal = (n_local_nets * n_var_net) + 1
        for t_edge in l_edges:
            l_output_variables = [4 + cont_output_variable, 5 + cont_output_variable]
            # generate coupling function
            coupling_function = " " + " ∧ ".join(map(str, l_output_variables)) + " "
            # generate the directed-edge object
            o_directed_edge = DirectedEdge(
                index_variable_signal,
                t_edge[1],
                t_edge[0],
                l_output_variables,
                coupling_function,
            )
            # add the directed object to list
            l_directed_edges.append(o_directed_edge)
            # updating the count of variables
            cont_output_variable += 5
            # updating the index variable signal
            index_variable_signal += 1

        # CREATE THE LAST EDGE
        # generate the last edge between the last network and the first
        l_edges.append((n_local_networks, 1))
        t_edge = (n_local_networks, 1)
        l_output_variables = [
            ((n_local_nets - 1) * n_var_net) + 3,
            ((n_local_nets - 1) * n_var_net) + 4,
        ]
        coupling_function = " " + " ∨ ".join(map(str, l_output_variables)) + " "
        o_directed_edge = DirectedEdge(
            index_variable_signal,
            t_edge[1],
            t_edge[0],
            l_output_variables,
            coupling_function,
        )
        l_directed_edges.append(o_directed_edge)

        # Update the first network
        # update_network = l_local_networks[0]
        # update_network.external_variables = [index_variable_signal]
        # # update_network.total_variables.append(index_variable_signal)
        # update_network.total_variables_count += 1

        # CREATE THE DYNAMIC OF THE LOCAL NETWORKS
        # Generate the functions for every variable in the CBN
        d_var_cnf_func = {}
        count_network = 1
        count_var = 0
        for o_local_network in l_local_networks:
            d_var_cnf_func[count_var + 1] = [
                [count_var + 2, -(count_var + 3), count_var + 4]
            ]
            d_var_cnf_func[count_var + 2] = [
                [count_var + 2, -(count_var + 3), -(count_var + 4)],
                [count_var + 5],
            ]
            d_var_cnf_func[count_var + 3] = [
                [-(count_var + 2), -(count_var + 4), count_var + 4],
                [count_var + 5],
            ]
            if o_local_network.index == 1:
                d_var_cnf_func[count_var + 4] = [
                    [count_var + 3, count_var + 5, index_variable_signal]
                ]
                d_var_cnf_func[count_var + 5] = [
                    [count_var + 1, count_var + 2, index_variable_signal]
                ]
            else:
                d_var_cnf_func[count_var + 4] = [
                    [
                        count_var + 1,
                        count_var + 2,
                        n_total_var + o_local_network.index - 1,
                    ]
                ]
                d_var_cnf_func[count_var + 5] = [
                    [
                        -(count_var + 1),
                        count_var + 2,
                        n_total_var + o_local_network.index - 1,
                    ]
                ]
            count_var += 5
            count_network += 1

        # generating the local network dynamic
        for o_local_network in l_local_networks:
            input_signals = DirectedEdge.find_input_edges_by_network_index(
                o_local_network.l_index, l_directed_edges
            )
            o_local_network.process_input_signals(input_signals)
            for i_local_variable in o_local_network.internal_variables:
                o_variable_model = InternalVariable(
                    i_local_variable, d_var_cnf_func[i_local_variable]
                )
                o_local_network.descriptive_function_variables.append(o_variable_model)

        # generating the CBN network object
        o_cbn = CBN(l_local_networks, l_directed_edges)

        # Find attractors
        o_cbn.find_local_attractors_heap()
        # find the compatible pairs
        o_cbn.find_compatible_pairs()
        # Find attractor fields
        o_cbn.mount_stable_attractor_fields()

        # collect indicators
        d_collect_indicators = {
            # initial parameters
            "i_sample": i_sample,
            "N_LOCAL_NETWORKS": n_local_networks,
            "N_VAR_NETWORK": n_var_network,
            "V_TOPOLOGY": v_topology,
            "N_OUTPUT_VARIABLES": n_output_variables,
            "N_CLAUSES_FUNCTION": n_clauses_function,
            # calculate parameters
            "n_local_attractors": o_cbn.get_n_local_attractors(),
            "n_pair_attractors": o_cbn.get_n_pair_attractors(),
            "n_attractor_fields": o_cbn.get_n_attractor_fields(),
        }
        l_data_sample.append(d_collect_indicators)
        # show the important outputs
        # o_cbn.show_resume()
CustomText.print_duplex_line()
# Take the time of the experiment
v_end_exp = time.time()
v_time_exp = v_end_exp - v_begin_exp
print("Time experiment (in seconds): ", v_time_exp)

# Save the collected indicator to profiler_analysis
pf_res = pd.DataFrame(l_data_sample)
pf_res.reset_index(drop=True, inplace=True)

# Save the experiment data in csv, using pandas Dataframe
path = "exp4_manual.csv"
pf_res.to_csv(path)
print("Experiment saved in:", path)

print("End experiment")
