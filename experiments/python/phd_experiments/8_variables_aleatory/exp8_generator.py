# external imports
import os
import pickle
import time

import pandas as pd

from classes.cbnetwork import CBN
from classes.globaltopology import GlobalTopology
# local imports
from classes.localtemplates import LocalNetworkTemplate
from classes.utils.customtext import CustomText

# experiment parameters
N_SAMPLES = 1000
N_LOCAL_NETWORKS = 5
N_EDGES = 5
N_VARIABLE_NET_MIN = 5
N_VARIABLE_NET_MAX = 25
N_OUTPUT_VARIABLES = 2
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 2
N_CLAUSES_FUNCTION = 2
N_LITERALS = 2

# Begin the Experiment
print("BEGIN THE EXPERIMENT")
print("=" * 50)

# Capture the time for all the experiment
v_begin_exp = time.time()

# Experiment Name
EXPERIMENT_NAME = "exp8_data"

# Create the 'outputs' directory if it doesn't exist
OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Create an experiment directory by parameters
DIRECTORY_PATH = (
    f"{OUTPUT_FOLDER}/{EXPERIMENT_NAME}_"
    f"{N_VARIABLE_NET_MIN}_{N_VARIABLE_NET_MAX}_{N_SAMPLES}"
)
os.makedirs(DIRECTORY_PATH, exist_ok=True)

# Create a directory to save the pkl files
DIRECTORY_PKL = os.path.join(DIRECTORY_PATH, "pkl_cbn")
os.makedirs(DIRECTORY_PKL, exist_ok=True)

# Generate the experiment data file in csv
file_path = os.path.join(DIRECTORY_PATH, "data.csv")

# Erase the file if it exists
if os.path.exists(file_path):
    os.remove(file_path)
    print("Existing file deleted:", file_path)

# Begin the process
for i_sample in range(1, N_SAMPLES + 1):
    # Generate the global topology object
    o_global_topology = GlobalTopology.generate_sample_topology(
        v_topology=V_TOPOLOGY, n_nodes=N_LOCAL_NETWORKS
    )

    for n_vars_network in range(N_VARIABLE_NET_MIN, N_VARIABLE_NET_MAX + 1, 5):
        # Generate the aleatory local network template object
        o_template = LocalNetworkTemplate(
            n_vars_network=n_vars_network,
            n_input_variables=N_INPUT_VARIABLES,
            n_output_variables=N_OUTPUT_VARIABLES,
            n_max_of_clauses=N_CLAUSES_FUNCTION,
            n_max_of_literals=N_LITERALS,
            v_topology=V_TOPOLOGY,
        )

        print(f"Experiment {i_sample} of {N_SAMPLES} - Topology: {V_TOPOLOGY}")
        print(f"Networks: {N_LOCAL_NETWORKS} Variables Min: {N_VARIABLE_NET_MIN}")
        print(
            f"Variables Max: {N_VARIABLE_NET_MAX} Current Variables: {n_vars_network}"
        )

        # Generate the CBN with the topology and template
        o_cbn = CBN.generate_cbn_from_template(
            v_topology=V_TOPOLOGY,
            n_local_networks=N_LOCAL_NETWORKS,
            n_vars_network=n_vars_network,
            o_template=o_template,
            l_global_edges=o_global_topology.l_edges,
        )

        # Find attractors
        v_begin_find_attractors = time.time()
        o_cbn.find_local_attractors_sequential()
        v_end_find_attractors = time.time()
        n_time_find_attractors = v_end_find_attractors - v_begin_find_attractors

        # Find the compatible pairs
        v_begin_find_pairs = time.time()
        o_cbn.find_compatible_pairs()
        v_end_find_pairs = time.time()
        n_time_find_pairs = v_end_find_pairs - v_begin_find_pairs

        # Find attractor fields
        v_begin_find_fields = time.time()
        o_cbn.mount_stable_attractor_fields()
        v_end_find_fields = time.time()
        n_time_find_fields = v_end_find_fields - v_begin_find_fields

        # Collect indicators
        d_collect_indicators = {
            # Initial parameters
            "i_sample": i_sample,
            "n_local_networks": N_LOCAL_NETWORKS,
            "n_var_network": n_vars_network,
            "v_topology": V_TOPOLOGY,
            "n_output_variables": N_OUTPUT_VARIABLES,
            "n_clauses_function": N_CLAUSES_FUNCTION,
            "n_edges": N_EDGES,
            # Calculated parameters
            "n_local_attractors": o_cbn.get_n_local_attractors(),
            "n_pair_attractors": o_cbn.get_n_pair_attractors(),
            "n_attractor_fields": o_cbn.get_n_attractor_fields(),
            # Time parameters
            "n_time_find_attractors": n_time_find_attractors,
            "n_time_find_pairs": n_time_find_pairs,
            "n_time_find_fields": n_time_find_fields,
        }

        # Save the collected indicators to CSV
        pf_res = pd.DataFrame(
            [d_collect_indicators]
        )  # Wrap in list to create a single-row DataFrame
        pf_res.to_csv(
            file_path, mode="a", header=not os.path.exists(file_path), index=False
        )

        print("Experiment data saved in:", file_path)

        # Save the object to a pickle file
        pickle_path = (
            f"{DIRECTORY_PKL}/cbn_{i_sample}_{N_LOCAL_NETWORKS}_{n_vars_network}.pkl"
        )
        with open(pickle_path, "wb") as file:
            pickle.dump(o_cbn, file)

        print("Pickle object saved in:", pickle_path)

        CustomText.print_duplex_line()
    CustomText.print_stars()
CustomText.print_dollars()

# Take the time of the experiment
v_end_exp = time.time()
v_time_exp = v_end_exp - v_begin_exp
print("Time experiment (in seconds): ", v_time_exp)

print("=" * 50)
print("END EXPERIMENT")
