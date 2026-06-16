# external imports
import os
import pickle
import time

import pandas as pd

from classes.cbnetwork import CBN
from classes.globaltopology import GlobalTopology
# Local imports
from classes.localtemplates import LocalNetworkTemplate
from classes.utils.customtext import CustomText

# Experiment parameters
N_SAMPLES = 1001
N_LOCAL_NETWORKS_MIN = 3
N_LOCAL_NETWORKS_MAX = 8
N_VAR_NETWORK = 5
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
EXPERIMENT_NAME = "exp7_data"

# Create the 'outputs' directory if it doesn't exist
OUTPUT_FOLDER = "outputs"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Create an experiment directory by parameters
DIRECTORY_PATH = (
    f"{OUTPUT_FOLDER}/{EXPERIMENT_NAME}_"
    f"{N_LOCAL_NETWORKS_MIN}_{N_LOCAL_NETWORKS_MAX}_{N_SAMPLES}"
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
    # Generate the aleatory local network template object
    o_template = LocalNetworkTemplate(
        n_vars_network=N_VAR_NETWORK,
        n_input_variables=N_INPUT_VARIABLES,
        n_output_variables=N_OUTPUT_VARIABLES,
        n_max_of_clauses=N_CLAUSES_FUNCTION,
        n_max_of_literals=N_LITERALS,
        v_topology=V_TOPOLOGY,
    )

    for n_local_networks in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        # Generate the global topology object
        o_global_topology = GlobalTopology.generate_sample_topology(
            v_topology=V_TOPOLOGY, n_nodes=n_local_networks
        )
        # Calculate the range of edges
        v_begin_edges = n_local_networks
        v_end_edges = n_local_networks + (n_local_networks // 2) + 1

        for n_edges in range(v_begin_edges, v_end_edges):
            print(f"Experiment {i_sample} of {N_SAMPLES} - Topology: {V_TOPOLOGY}")
            print(f"Networks: {n_local_networks} Variables: {N_VAR_NETWORK}")
            print(f"Current edges: {n_edges}")

            # Generate the CBN with the topology and template
            o_cbn = CBN.generate_cbn_from_template(
                v_topology=V_TOPOLOGY,
                n_local_networks=n_local_networks,
                n_vars_network=N_VAR_NETWORK,
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
                "n_local_networks": n_local_networks,
                "n_var_network": N_VAR_NETWORK,
                "v_topology": V_TOPOLOGY,
                "n_output_variables": N_OUTPUT_VARIABLES,
                "n_clauses_function": N_CLAUSES_FUNCTION,
                "n_edges": n_edges,
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
                f"{DIRECTORY_PKL}/cbn_{i_sample}_{n_local_networks}_{n_edges}.pkl"
            )
            with open(pickle_path, "wb") as file:
                pickle.dump(o_cbn, file)

            print("Pickle object saved in:", pickle_path)

            # add edge - update the topology
            o_global_topology.generate_edge()

            CustomText.print_duplex_line()
        CustomText.print_stars()
    CustomText.print_dollars()

# Take the time of the experiment
v_end_exp = time.time()
v_time_exp = v_end_exp - v_begin_exp
print("Time experiment (in seconds): ", v_time_exp)

print("=" * 50)
print("END EXPERIMENT")
