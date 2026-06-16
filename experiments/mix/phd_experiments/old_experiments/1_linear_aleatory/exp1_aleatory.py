# external imports
import time

import pandas as pd

# local imports
from classes.cbnetwork import CBN
from classes.utils.customtext import CustomText

"""
Test the linear structure 
using aleatory generated networks
number of local networks 3 - 10 
"""

# experiment parameters
N_SAMPLES = 100
N_LOCAL_NETWORKS_MIN = 3
N_LOCAL_NETWORKS_MAX = 10
N_VAR_NETWORK = 5
N_OUTPUT_VARIABLES = 2
V_TOPOLOGY = 4  # path graph
N_CLAUSES_FUNCTION = 2

# Begin Experiment

# Capture the time for all the experiment
v_begin_exp = time.time()

# Begin the process
l_data_sample = []
for n_local_networks in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX):
    for i_sample in range(1, N_SAMPLES + 1):
        print("Experiment", i_sample, "of", N_SAMPLES)
        # generate a Coupled Boolean Network with the parameters
        o_cbn = CBN.generate_aleatory_cbn_by_topology(
            n_local_networks=n_local_networks,
            n_var_network=N_VAR_NETWORK,
            v_topology=V_TOPOLOGY,
            n_output_variables=N_OUTPUT_VARIABLES,
        )

        # Find attractors
        v_begin_find_attractors = time.time()
        o_cbn.find_local_attractors_heap()
        v_end_find_attractors = time.time()
        n_time_find_attractors = v_end_find_attractors - v_begin_find_attractors

        # find the compatible pairs
        v_begin_find_pairs = time.time()
        o_cbn.find_compatible_pairs()
        v_end_find_pairs = time.time()
        n_time_find_pairs = v_end_find_pairs - v_begin_find_pairs

        # Find attractor fields
        v_begin_find_fields = time.time()
        o_cbn.mount_stable_attractor_fields()
        v_end_find_fields = time.time()
        n_time_find_fields = v_end_find_fields - v_begin_find_fields

        # collect indicators
        d_collect_indicators = {
            # initial parameters
            "i_sample": i_sample,
            "N_LOCAL_NETWORKS": n_local_networks,
            "N_VAR_NETWORK": N_VAR_NETWORK,
            "V_TOPOLOGY": V_TOPOLOGY,
            "N_OUTPUT_VARIABLES": N_OUTPUT_VARIABLES,
            "N_CLAUSES_FUNCTION": N_CLAUSES_FUNCTION,
            # time parameters
            "n_time_find_attractors": n_time_find_attractors,
            "n_time_find_pairs": n_time_find_pairs,
            "n_time_find_fields": n_time_find_fields,
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
path = "exp1_aleatory.csv"
pf_res.to_csv(path)
print("Experiment saved in:", path)

print("End experiment")
