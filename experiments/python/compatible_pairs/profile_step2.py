import cProfile
import pstats
import io
from cbnetwork.cbnetwork import CBN
from cbnetwork.globaltopology import GlobalTopology

def profile_step2():
    # Larger system to stress Step 2
    n_nets = 6
    n_vars = 13 # 8192 states per network-scene
    top_id = 1  # Complete
    
    print(f"Generating system: {n_nets} nets, {n_vars} vars...")
    o_cbn = CBN.cbn_generator(
        v_topology=top_id,
        n_local_networks=n_nets,
        n_vars_network=n_vars,
        n_input_variables=2,
        n_output_variables=2,
        n_max_of_clauses=3,
        n_max_of_literals=2
    )

    print("Finding attractors (Turbo)...")
    o_cbn.find_local_attractors_brute_force_turbo_sequential()
    
    print("Profiling find_compatible_pairs...")
    pr = cProfile.Profile()
    pr.enable()
    o_cbn.find_compatible_pairs()
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats(20)
    print(s.getvalue())

if __name__ == "__main__":
    profile_step2()
