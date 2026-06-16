import logging
import sys
import copy
from cbnetwork.cbnetwork import CBN
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.utils.customtext import CustomText

# 1. Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)

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

def verify_consistency_dynamic(o_cbn_sat, o_cbn_bf):
    """Compare attractor signatures between two processed CBN objects."""
    CustomText.make_sub_sub_title("Consistency Verification: SAT vs Brute Force")
    
    sigs_sat = extract_attractor_signatures(o_cbn_sat)
    sigs_bf = extract_attractor_signatures(o_cbn_bf)
    
    mismatches = []
    for net_index in sigs_sat:
        s_sat = sigs_sat[net_index]
        s_bf = sigs_bf[net_index]
        
        if s_sat != s_bf:
            mismatches.append(net_index)
            logging.error(f"  [MISMATCH] Network {net_index}:")
            
            # Find which scenes mismatch
            all_scenes = set(s_sat.keys()) | set(s_bf.keys())
            for scene in sorted(list(all_scenes)):
                v_sat = s_sat.get(scene)
                v_bf = s_bf.get(scene)
                if v_sat != v_bf:
                    logging.info(f"    Scene {scene}:")
                    logging.info(f"      SAT: {v_sat}")
                    logging.info(f"      BF:  {v_bf}")
            # Stop after first mismatching network to avoid spam
            break

    if not mismatches:
        logging.info("  [SUCCESS] All local networks yielded identical attractor signatures in all scenes.")
        return True
    else:
        logging.error(f"  [FAILURE] Mismatches found in networks: {mismatches}")
        return False

def main():
    CustomText.make_principal_title("SCALED VERIFICATION: 6-NETWORK COMPLETE GRAPH")
    
    # Configuration based on 1_complete.ipynb
    N_LOCAL_NETWORKS = 6
    N_VAR_NETWORK = 5
    N_INPUT_VARIABLES = 2
    N_OUTPUT_VARIABLES = 2
    V_TOPOLOGY = 1 # Complete Digraph
    N_MAX_CLAUSES = 2
    N_MAX_LITERALS = 2

    logging.info(f"Generating Aleatory CBN with {N_LOCAL_NETWORKS} networks (Complete Topology)...")
    
    # Generate the system
    o_cbn_sat = CBN.cbn_generator(
        v_topology=V_TOPOLOGY,
        n_vars_network=N_VAR_NETWORK,
        n_local_networks=N_LOCAL_NETWORKS,
        n_input_variables=N_INPUT_VARIABLES,
        n_output_variables=N_OUTPUT_VARIABLES,
        n_max_of_clauses=N_MAX_CLAUSES,
        n_max_of_literals=N_MAX_LITERALS
    )
    
    # Clone for Brute Force (to ensure same logic/topology)
    o_cbn_bf = copy.deepcopy(o_cbn_sat)
    
    # 1. Process with SAT (Sequential for clarity)
    CustomText.make_sub_title("Phase 1: SAT-based Attractor Finding")
    o_cbn_sat.find_local_attractors_sequential()
    
    # 2. Process with Brute Force (Sequential for clarity)
    CustomText.make_sub_title("Phase 2: Brute Force Attractor Finding")
    o_cbn_bf.find_local_attractors_brute_force_sequential()

    # 3. Verify Results
    if verify_consistency_dynamic(o_cbn_sat, o_cbn_bf):
        print("\n" + "="*80)
        print(" FINAL VERIFICATION SUCCESS: 6-network complete graph validated.")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print(" FINAL VERIFICATION FAILURE: Discrepancies detected.")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
