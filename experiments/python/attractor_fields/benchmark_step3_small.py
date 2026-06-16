import logging
import time
from cbnetwork.cbnetwork import CBN
from cbnetwork.globaltopology import GlobalTopology

def setup_logger():
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s:%(name)s:%(message)s')

def run_benchmark_step3_small():
    setup_logger()
    
    # Very small system to get results quickly
    n_nets = 4
    n_vars = 6
    top_id = 1  # Complete
    
    print(f"\nBenchmark Step 3: {n_nets} networks, {n_vars} vars each")
    print(f"{'Method':<30} | {'Time':<10} | {'Fields'}")
    print("-" * 60)

    # Generate System
    o_cbn = CBN.cbn_generator(
        v_topology=top_id,
        n_local_networks=n_nets,
        n_vars_network=n_vars,
        n_input_variables=2,
        n_output_variables=2,
        n_max_of_clauses=3,
        n_max_of_literals=2
    )

    # STEP 1 (Turbo)
    o_cbn.find_local_attractors_brute_force_turbo_sequential()
    
    # STEP 2 (Sequential)
    o_cbn.find_compatible_pairs()
    
    # STEP 3 - Sequential
    start = time.time()
    o_cbn.mount_stable_attractor_fields()
    seq_time = time.time() - start
    seq_fields = len(o_cbn.d_attractor_fields)
    print(f"{'Sequential':<30} | {seq_time:>9.3f}s | {seq_fields}")

    # STEP 3 - Parallel
    start = time.time()
    o_cbn.mount_stable_attractor_fields_parallel(num_cpus=4)
    par_time = time.time() - start
    par_fields = len(o_cbn.d_attractor_fields)
    print(f"{'Parallel (4 CPUs)':<30} | {par_time:>9.3f}s | {par_fields}")

    # STEP 3 - Turbo (Numba) with warmup
    o_cbn.mount_stable_attractor_fields_turbo()  # Warmup
    
    start = time.time()
    o_cbn.mount_stable_attractor_fields_turbo()
    turbo_time = time.time() - start
    turbo_fields = len(o_cbn.d_attractor_fields)
    print(f"{'Turbo (Numba)':<30} | {turbo_time:>9.3f}s | {turbo_fields}")

    # Check consistency
    if seq_fields == par_fields == turbo_fields:
        print(f"\n✓ All methods: {seq_fields} fields (consistent)")
        print(f"\nSpeedup vs Sequential:")
        print(f"  Parallel: {seq_time/par_time:.2f}x")
        print(f"  Turbo:    {seq_time/turbo_time:.2f}x")
    else:
        print(f"\n⚠ MISMATCH: Seq={seq_fields}, Par={par_fields}, Turbo={turbo_fields}")

if __name__ == "__main__":
    run_benchmark_step3_small()
