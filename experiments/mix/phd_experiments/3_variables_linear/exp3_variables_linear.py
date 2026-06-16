# external imports
import os
import pickle
import time

import pandas as pd

# local imports
from classes.cbnetwork import CBN
from classes.utils.customtext import CustomText

"""
Experiment 3 - Test the CBN with Linear Topology using aleatory generated template for the local network
growing the number of variables os local networks.  
"""

# experiment parameters
N_SAMPLES = 1000
N_LOCAL_NETWORKS = 5
N_VARIABLE_NET_MIN = 5
N_VARIABLE_NET_MAX = 30
N_OUTPUT_VARIABLES = 2
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4
N_CLAUSES_FUNCTION = 2

# verbose parameters
SHOW_MESSAGES = True

# Begin the Experiment
print("BEGIN THE EXPERIMENT")
print("=" * 80)

# Capture the time for all the experiment
v_begin_exp = time.time()

# Experiment Name
EXPERIMENT_NAME = "exp3_variables_linear"

# Create the 'outputs' directory if it doesn't exist
OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# create an experiment directory by parameters
DIRECTORY_PATH = (
    OUTPUT_FOLDER
    + "/"
    + EXPERIMENT_NAME
    + "_"
    + str(N_VARIABLE_NET_MIN)
    + "_"
    + str(N_VARIABLE_NET_MAX)
    + "_"
    + str(N_SAMPLES)
)
os.makedirs(DIRECTORY_PATH, exist_ok=True)

# create a directory to save the pkl files
DIRECTORY_PKL = DIRECTORY_PATH + "/pkl_cbn"
os.makedirs(DIRECTORY_PKL, exist_ok=True)

# generate the experiment data file in csv
file_path = DIRECTORY_PATH + "/data.csv"

# Erase the file if exists
if os.path.exists(file_path):
    os.remove(file_path)
    print("Existing file deleted:", file_path)

# Begin the process
for i_sample in range(1, N_SAMPLES + 1):  # 1 - 100
    for N_VAR_NETWORK in [
        i for i in range(N_VARIABLE_NET_MIN, N_VARIABLE_NET_MAX + 1, 5)
    ]:

        l_data_sample = []
        print("Experiment", i_sample, "of", N_SAMPLES, " TOPOLOGY:", V_TOPOLOGY)

        # generate aleatory CBN by topology
        o_cbn = CBN.generate_aleatory_cbn_by_topology(
            n_local_networks=N_LOCAL_NETWORKS,
            n_var_network=N_VAR_NETWORK,
            v_topology=V_TOPOLOGY,
            n_output_variables=N_OUTPUT_VARIABLES,
        )

        # find attractors
        v_begin_find_attractors = time.time()
        o_cbn.find_local_attractors_sequential()
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
            "n_local_networks": N_LOCAL_NETWORKS,
            "n_var_network": N_VAR_NETWORK,
            "v_topology": V_TOPOLOGY,
            "n_output_variables": N_OUTPUT_VARIABLES,
            "n_clauses_function": N_CLAUSES_FUNCTION,
            # calculate parameters
            "n_local_attractors": o_cbn.get_n_local_attractors(),
            "n_pair_attractors": o_cbn.get_n_pair_attractors(),
            "n_attractor_fields": o_cbn.get_n_attractor_fields(),
            # time parameters
            "n_time_find_attractors": n_time_find_attractors,
            "n_time_find_pairs": n_time_find_pairs,
            "n_time_find_fields": n_time_find_fields,
        }
        l_data_sample.append(d_collect_indicators)

        # save the collected indicator to profiler_analysis
        pf_res = pd.DataFrame(l_data_sample)
        pf_res.reset_index(drop=True, inplace=True)

        # if the file exists, open it in 'a' mode (append), else create a new file
        mode = "a" if os.path.exists(file_path) else "w"
        # Add the header only if it's a new file
        header = False if mode == "a" else True
        # save the data to the CSV file only if there is data in pf_res
        if not pf_res.empty:
            pf_res.to_csv(file_path, mode=mode, header=header, index=False)
            print("Experiment data saved in:", file_path)
        else:
            print("No data to save in:", file_path)

        # Open a file in binary write mode (wb)
        pickle_path = (
            DIRECTORY_PKL
            + "/cbn_"
            + str(i_sample)
            + "_"
            + str(V_TOPOLOGY)
            + "_"
            + str(N_LOCAL_NETWORKS)
            + "_"
            + str(N_VAR_NETWORK)
            + ".pkl"
        )
        with open(pickle_path, "wb") as file:
            # Use pickle.dump to save the object to the file
            pickle.dump(o_cbn, file)

        # Close the file
        file.close()
        print("Pickle object saved in:", pickle_path)

        CustomText.print_duplex_line()
        CustomText.print_stars()
    CustomText.print_dollars()

# Take the time of the experiment
v_end_exp = time.time()
v_time_exp = v_end_exp - v_begin_exp
print("Time experiment (in seconds): ", v_time_exp)

print("=" * 80)
print("END EXPERIMENT")
