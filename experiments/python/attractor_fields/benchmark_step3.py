import logging
import time
import os
import sys
from cbnetwork.cbnetwork import CBN
from cbnetwork.globaltopology import GlobalTopology

def setup_logger():
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s:%(name)s:%(message)s')
    logger = logging.getLogger("benchmark_step3")
    logger.setLevel(logging.INFO)
    return logger

def run_benchmark_step3():
    logger = setup_logger()
    
    # Test with a smaller system first (Step 3 can be very slow)
    n_nets = 5
    n_vars = 8
    topologies = [1]  # Complete - generates many fields
    
    print(f"{'Topology':<20} | {'Method':<30} | {'Time':<10} | {'Fields'}")
    print("-" * 85)

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

        # 2. RUN STEP 1 (Turbo)
        o_cbn.find_local_attractors_brute_force_turbo_sequential()
        
        # 3. RUN STEP 2 (Sequential - fastest)
        o_cbn.find_compatible_pairs()
        
        # Helper to count total fields
        def count_fields(cbn):
            return len(cbn.d_attractor_fields)

        # 4. Benchmark Step 3 - Sequential
        start = time.time()
        o_cbn.mount_stable_attractor_fields()
        seq_time = time.time() - start
        seq_fields = count_fields(o_cbn)
        print(f"{top_name:<20} | {'Sequential':<30} | {seq_time:>9.3f}s | {seq_fields}")

        # 5. Benchmark Step 3 - Parallel
        start = time.time()
        o_cbn.mount_stable_attractor_fields_parallel(num_cpus=4)
        par_time = time.time() - start
        par_fields = count_fields(o_cbn)
        print(f"{top_name:<20} | {'Parallel (4 CPUs)':<30} | {par_time:>9.3f}s | {par_fields}")

        # 6. Benchmark Step 3 - Parallel Chunks
        start = time.time()
        o_cbn.mount_stable_attractor_fields_parallel_chunks(num_cpus=4)
        par_chunks_time = time.time() - start
        par_chunks_fields = count_fields(o_cbn)
        print(f"{top_name:<20} | {'Parallel Chunks (4 CPUs)':<30} | {par_chunks_time:>9.3f}s | {par_chunks_fields}")

        # 7. Benchmark Step 3 - Turbo (Numba)
        # Warmup
        o_cbn.mount_stable_attractor_fields_turbo()
        
        start = time.time()
        o_cbn.mount_stable_attractor_fields_turbo()
        turbo_time = time.time() - start
        turbo_fields = count_fields(o_cbn)
        print(f"{top_name:<20} | {'Turbo (Numba)':<30} | {turbo_time:>9.3f}s | {turbo_fields}")

        # Consistency check
        if not (seq_fields == par_fields == par_chunks_fields == turbo_fields):
            print(f"WARNING: Field count mismatch!")
            print(f"  Seq={seq_fields}, Par={par_fields}, ParChunks={par_chunks_fields}, Turbo={turbo_fields}")
        else:
            print(f"\n✓ All methods produced {seq_fields} fields consistently\n")

if __name__ == "__main__":
    run_benchmark_step3()
