import logging
import sys
import copy
from cbnetwork.cbnetwork import CBN
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.utils.customtext import CustomText

# 1. Setup Logging
logging.basicConfig(
    level=logging.ERROR, # Higher level to keep output clean, we will use logging.info for main flow
    format='%(message)s',
    stream=sys.stdout
)

# Custom logger for the verification flow
logger = logging.getLogger("verifier")
logger.setLevel(logging.INFO)

def extract_attractor_signatures(o_cbn):
    """Return a dictionary: {net_index: {scene_values: sorted_attractors}}"""
    extracted = {}
    for net in o_cbn.l_local_networks:
        net_sigs = {}
        for scene in net.local_scenes:
            # Use the string representation of scene values as key
            scene_key = "".join(map(str, scene.l_values))
            scene_sigs = []
            for attr in scene.l_attractors:
                # Normalize state values: only take first N elements (internal variables)
                n_internal = len(net.internal_variables)
                states = tuple(
                    tuple(int(v) for v in s.l_variable_values[:n_internal]) for s in attr.l_states
                )
                if len(states) > 1:
                    rotations = [tuple(states[i:] + states[:i]) for i in range(len(states))]
                    states = min(rotations)
                scene_sigs.append(states)
            net_sigs[scene_key] = tuple(sorted(scene_sigs))
        extracted[net.index] = net_sigs
    return extracted

def verify_topology(topology_id, topology_name):
    CustomText.make_sub_title(f"TOPOLOGY: {topology_name} (ID={topology_id})")
    
    N_LOCAL_NETWORKS = 6
    N_VAR_NETWORK = 5
    N_INPUT_VARIABLES = 2
    N_OUTPUT_VARIABLES = 2
    N_MAX_CLAUSES = 2
    N_MAX_LITERALS = 2

    # Generate the system
    o_cbn_sat = CBN.cbn_generator(
        v_topology=topology_id,
        n_vars_network=N_VAR_NETWORK,
        n_local_networks=N_LOCAL_NETWORKS,
        n_input_variables=N_INPUT_VARIABLES,
        n_output_variables=N_OUTPUT_VARIABLES,
        n_max_of_clauses=N_MAX_CLAUSES,
        n_max_of_literals=N_MAX_LITERALS
    )
    
    o_cbn_bf = copy.deepcopy(o_cbn_sat)
    
    # 1. Process with SAT
    o_cbn_sat.find_local_attractors_sequential()
    
    # 2. Process with Brute Force
    o_cbn_bf.find_local_attractors_brute_force_sequential()

    # 3. Extract and Compare
    sigs_sat = extract_attractor_signatures(o_cbn_sat)
    sigs_bf = extract_attractor_signatures(o_cbn_bf)
    
    mismatches = []
    for net_index in sigs_sat:
        if sigs_sat[net_index] != sigs_bf[net_index]:
            mismatches.append(net_index)
            logger.error(f"  [MISMATCH] Topology: {topology_name}, Network Index: {net_index}")
            
            # Detailed Scene Comparison
            s_sat = sigs_sat[net_index]
            s_bf = sigs_bf[net_index]
            all_scenes = sorted(list(set(s_sat.keys()) | set(s_bf.keys())))
            
            for scene_key in all_scenes:
                v_sat = s_sat.get(scene_key)
                v_bf = s_bf.get(scene_key)
                if v_sat != v_bf:
                    logger.error(f"    Scene {scene_key}:")
                    logger.error(f"      SAT Attractors: {v_sat}")
                    logger.error(f"      BF Attractors:  {v_bf}")
            
            # Dump Network Logic for the failing network
            failing_net = next(n for n in o_cbn_sat.l_local_networks if n.index == net_index)
            logger.error(f"    Network Logic (CNF):")
            for var in failing_net.descriptive_function_variables:
                logger.error(f"      Var {var.index}: {var.cnf_function}")
            logger.error(f"    External Variables: {failing_net.external_variables}")
            
    if not mismatches:
        logger.info(f"  [SUCCESS] '{topology_name}' verified. Perfect match.")
        return True
    else:
        return False

def main():
    CustomText.make_principal_title("MULTI-TOPOLOGY SCALE VERIFICATION (6 NETWORKS)")
    
    topologies = [
        (3, "Cycle"),
        (4, "Linear/Path"),
        (7, "Dorogovtsev-Mendes"),
        (8, "Small World"),
        (9, "Scale Free"),
        (10, "Random")
    ]

    all_passed = True
    results = []

    for top_id, top_name in topologies:
        passed = verify_topology(top_id, top_name)
        results.append((top_name, passed))
        if not passed:
            all_passed = False

    print("\n" + "="*80)
    print(" SUMMARY OF TOPOLOGY VERIFICATION")
    print("-"*80)
    for name, ok in results:
        status = "PASSED" if ok else "FAILED"
        print(f" {name:<25}: {status}")
    print("="*80 + "\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
