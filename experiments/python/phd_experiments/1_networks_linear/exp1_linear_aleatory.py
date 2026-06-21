import json
import sys
import time
from pathlib import Path

# Add project root to sys.path to allow importing from cbn_python/src
root_dir = Path(__file__).resolve().parents[4]
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.localtemplates import PathCircleTemplate
from cbnetwork.utils.customtext import CustomText

"""
Experiment 1 - Test the path and 3_ring_aleatory structures 
using aleatory generated template for the local network.
DEFINITIVE REFACTOR: Established master JSON contract with self-describing topology.
"""

# experiment parameters
N_SAMPLES = 10
N_LOCAL_NETWORKS_MIN = 3
N_LOCAL_NETWORKS_MAX = 11
N_VAR_NETWORK = 5
N_OUTPUT_VARIABLES = 2
N_INPUT_VARIABLES = 2
V_TOPOLOGY = 4
N_CLAUSES_FUNCTION = 2

# Begin the Experiment
print("BEGIN THE EXPERIMENT")
print("=" * 80)

# Capture the time for all the experiment
v_begin_exp = time.time()

# Experiment Name
EXPERIMENT_NAME = "exp1_linear_aleatory"

# Create the 'outputs' directory if it doesn't exist using pathlib
OUTPUT_FOLDER = Path("outputs")
OUTPUT_FOLDER.mkdir(exist_ok=True)

# create an experiment directory by parameters
DIRECTORY_PATH = (
    OUTPUT_FOLDER
    / f"{EXPERIMENT_NAME}_{N_LOCAL_NETWORKS_MIN}_{N_LOCAL_NETWORKS_MAX}_{N_SAMPLES}"
)
DIRECTORY_PATH.mkdir(exist_ok=True)

# create a directory to save the JSON files
DIRECTORY_JSON = DIRECTORY_PATH / "json_data"
DIRECTORY_JSON.mkdir(exist_ok=True)

# generate the experiment metrics file in csv
metrics_path = DIRECTORY_PATH / "metrics.csv"

# Write header if it's a new file
if not metrics_path.exists():
    with metrics_path.open("w") as f:
        f.write(
            "i_sample,n_local_networks,n_var_network,v_topology,n_output_variables,n_clauses_function,"
            "n_local_attractors,n_pair_attractors,n_attractor_fields,"
            "n_time_find_attractors,n_time_find_pairs,n_time_find_fields\n"
        )

# Begin the process
for i_sample in range(1, N_SAMPLES + 1):
    # generate the aleatory local network template
    o_path_circle_template = PathCircleTemplate.generate_path_circle_template(
        n_var_network=N_VAR_NETWORK, n_input_variables=N_INPUT_VARIABLES
    )

    for n_local_networks in range(N_LOCAL_NETWORKS_MIN, N_LOCAL_NETWORKS_MAX + 1):
        print(
            f"Experiment {i_sample} of {N_SAMPLES} | Networks: {n_local_networks} | TOPOLOGY: {V_TOPOLOGY}"
        )

        o_cbn = o_path_circle_template.generate_cbn_from_template(
            v_topology=V_TOPOLOGY, n_local_networks=n_local_networks
        )

        # 1. find attractors (using brute force for scientific parity with C++)
        v_begin_find_attractors = time.time()
        # 1. find attractors (using Duvrova/SAT method for scalability)
        v_begin_find_attractors = time.time()
        o_cbn.find_attractors_duvrova()
        v_end_find_attractors = time.time()
        n_time_find_attractors = v_end_find_attractors - v_begin_find_attractors
        v_end_find_attractors = time.time()
        n_time_find_attractors = v_end_find_attractors - v_begin_find_attractors

        # 2. find the compatible pairs
        v_begin_find_pairs = time.time()
        o_cbn.find_compatible_pairs()
        v_end_find_pairs = time.time()
        n_time_find_pairs = v_end_find_pairs - v_begin_find_pairs

        # 3. Find attractor fields
        v_begin_find_fields = time.time()
        o_cbn.mount_stable_attractor_fields()
        v_end_find_fields = time.time()
        n_time_find_fields = v_end_find_fields - v_begin_find_fields

        # Data extraction and storage with the requested strict naming pattern
        base_name = f"sample_{i_sample}_topo_{V_TOPOLOGY}_nets_{n_local_networks}"

        # Metadata for self-describing topology
        metadata = {
            "n_input_variables": N_INPUT_VARIABLES,
            "n_output_variables": N_OUTPUT_VARIABLES,
            "v_topology": V_TOPOLOGY,
            "n_clauses_function": N_CLAUSES_FUNCTION,
            "coupling_function_type": "OR",  # Default for PathCircleTemplate
        }

        # Save structural data (Topology)
        with (DIRECTORY_JSON / f"{base_name}_topology.json").open("w") as f:
            json.dump(o_cbn.to_json_topology(metadata=metadata), f, indent=4)

        # Save attractor data
        with (DIRECTORY_JSON / f"{base_name}_attractors.json").open("w") as f:
            json.dump(o_cbn.to_json_attractors(), f, indent=4)

        # Save pairs data
        with (DIRECTORY_JSON / f"{base_name}_pairs.json").open("w") as f:
            json.dump(o_cbn.to_json_pairs(), f, indent=4)

        # Save fields data
        with (DIRECTORY_JSON / f"{base_name}_fields.json").open("w") as f:
            json.dump(o_cbn.to_json_fields(), f, indent=4)

        # Performance Tracking: append to metrics.csv
        with metrics_path.open("a") as f:
            metrics = [
                i_sample,
                n_local_networks,
                N_VAR_NETWORK,
                V_TOPOLOGY,
                N_OUTPUT_VARIABLES,
                N_CLAUSES_FUNCTION,
                o_cbn.get_n_local_attractors(),
                o_cbn.get_n_pair_attractors(),
                o_cbn.get_n_attractor_fields(),
                n_time_find_attractors,
                n_time_find_pairs,
                n_time_find_fields,
            ]
            f.write(",".join(map(str, metrics)) + "\n")

        print(f"Data and metrics saved for {base_name}")
        CustomText.print_duplex_line()
        CustomText.print_stars()
    CustomText.print_dollars()

# Take the time of the experiment
v_end_exp = time.time()
v_time_exp = v_end_exp - v_begin_exp
print("Time experiment (in seconds): ", v_time_exp)

print("=" * 80)
print("END EXPERIMENT")
