import cProfile
import pickle
import pstats

# select the most cost cbn
# path_cbn = '5_linear_circle/outputs/exp5_aleatory_linear_circle_8_8_10/cbn_9_3.pkl'
# path_cbn = 'exp5_aleatory_linear_circle_7_7_10/pkl_cbn/cbn_8_3.pkl'
# path_cbn = 'exp5_aleatory_linear_circle_7_7_10/pkl_cbn/cbn_10_3.pkl'
path_cbn = (
    "../outputs/2_0_data_slow/exp5_aleatory_linear_circle_3_3_10/pkl_cbn/cbn_10_4.pkl"
)

with open(path_cbn, "rb") as file:
    o_cbn = pickle.load(file)

# Show the CBN Information
o_cbn.show_description()

# Find Local attractors
o_cbn.find_local_attractors_heap()
o_cbn.show_local_attractors()

# Find attractor pairs
o_cbn.find_compatible_pairs()
o_cbn.show_attractor_pairs()

# Find stable attractor fields
# o_cbn.find_stable_attractor_fields()
# Run the profiler on the function
cProfile.run("o_cbn.mount_stable_attractor_fields()", "profile_stats")
o_cbn.show_stable_attractor_fields()

# Load the profile statistics
stats = pstats.Stats("profile_stats")
# Print the statistics
stats.print_stats()
print("end profile profiler_analysis")
