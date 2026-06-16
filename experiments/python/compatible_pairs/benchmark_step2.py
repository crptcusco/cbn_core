import logging
import time
import os
import sys
import numpy as np
from cbnetwork.cbnetwork import CBN
from cbnetwork.globaltopology import GlobalTopology

def setup_logger():
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s:%(name)s:%(message)s')
    logger = logging.getLogger("benchmark_step2")
    logger.setLevel(logging.INFO)
    return logger

def run_benchmark_step2():
    logger = setup_logger()
    
    n_nets = 8
    n_vars = 10
    # Complete topology (1) has the most edges, and thus the most compatible pairs calculations.
    topologies = [1] 
    
    print(f"{'Topology':<20} | {'Method':<20} | {'Time':<10} | {'Pairs'}")
    print("-" * 75)

    for top_id in topologies:
        top_name = GlobalTopology.allowed_topologies[top_id]
        
        # 1. Generate System
        o_cbn = CBN.cbn_generator(
            v_topology=top_id,
            n_local_networks=n_nets,
            n_vars_network=n_vars,
            n_input_variables=2,
            n_output_variables=2,
            n_max_of_clauses=3,
            n_max_of_literals=2
        )

        # 2. RUN STEP 1 (Turbo) - We need attractors first
        o_cbn.find_local_attractors_brute_force_turbo_sequential()
        
        # Helper to count total pairs
        def count_total_pairs(cbn):
            total = 0
            for net in cbn.l_local_networks:
                edges = cbn.get_output_edges_by_network_index(net.index)
                for edge in edges:
                    total += len(edge.d_comp_pairs_attractors_by_value[0])
                    total += len(edge.d_comp_pairs_attractors_by_value[1])
            return total

        # 3. Benchmark Step 2 - Sequential
        start = time.time()
        o_cbn.find_compatible_pairs()
        seq_time = time.time() - start
        seq_pairs = count_total_pairs(o_cbn)
        print(f"{top_name:<20} | {'Sequential':<20} | {seq_time:>9.3f}s | {seq_pairs}")

        # 4. Benchmark Step 2 - Parallel
        start = time.time()
        o_cbn.find_compatible_pairs_parallel(num_cpus=4)
        par_time = time.time() - start
        par_pairs = count_total_pairs(o_cbn)
        print(f"{top_name:<20} | {'Parallel (4 CPUs)':<20} | {par_time:>9.3f}s | {par_pairs}")

        # 5. Benchmark Step 2 - Turbo
        # Warmup
        o_cbn.find_compatible_pairs_turbo()
        
        start = time.time()
        o_cbn.find_compatible_pairs_turbo()
        turbo_time = time.time() - start
        turbo_pairs = count_total_pairs(o_cbn)
        print(f"{top_name:<20} | {'Turbo (Numba)':<20} | {turbo_time:>9.3f}s | {turbo_pairs}")

        if seq_pairs != turbo_pairs:
            print(f"WARNING: Pair count mismatch! Seq={seq_pairs}, Turbo={turbo_pairs}")
        if par_pairs != seq_pairs:
            print(f"WARNING: Pair count mismatch! Seq={seq_pairs}, Par={par_pairs}")

if __name__ == "__main__":
    run_benchmark_step2()
