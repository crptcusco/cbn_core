import logging
import time
from cbnetwork.cbnetwork import CBN

def run_tiny_benchmark():
    logging.basicConfig(level=logging.ERROR)
    
    # TINY system: 3 networks, 5 vars
    print("\n🔬 Benchmark Step 3: 3 networks, 5 vars each (Complete topology)")
    print(f"{'Method':<30} | {'Time':<10} | {'Fields'}")
    print("-" * 60)

    o_cbn = CBN.cbn_generator(
        v_topology=1,  # Complete
        n_local_networks=3,
        n_vars_network=5,
        n_input_variables=1,
        n_output_variables=1,
        n_max_of_clauses=2,
        n_max_of_literals=2
    )

    # STEP 1 + 2
    o_cbn.find_local_attractors_brute_force_turbo_sequential()
    o_cbn.find_compatible_pairs()
    
    # STEP 3 - Sequential
    start = time.time()
    o_cbn.mount_stable_attractor_fields()
    seq_time = time.time() - start
    seq_fields = len(o_cbn.d_attractor_fields)
    print(f"{'Sequential':<30} | {seq_time:>9.3f}s | {seq_fields}")

    # STEP 3 - Turbo (with warmup)
    o_cbn.mount_stable_attractor_fields_turbo()
    
    start = time.time()
    o_cbn.mount_stable_attractor_fields_turbo()
    turbo_time = time.time() - start
    turbo_fields = len(o_cbn.d_attractor_fields)
    print(f"{'Turbo (Numba)':<30} | {turbo_time:>9.3f}s | {turbo_fields}")

    if seq_fields == turbo_fields:
        speedup = seq_time / turbo_time if turbo_time > 0 else 0
        print(f"\n✓ Consistent: {seq_fields} fields")
        print(f"Speedup: {speedup:.2f}x")
    else:
        print(f"\n⚠ MISMATCH: Seq={seq_fields}, Turbo={turbo_fields}")

if __name__ == "__main__":
    run_tiny_benchmark()
