from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.internalvariable import InternalVariable


def _normalize_attractors(local_scenes):
    """Return a set of attractors where each attractor is a tuple of state-tuples of '0'/'1' strings."""
    result = set()
    for scene in local_scenes:
        for attr in scene.l_attractors:
            states = []
            for s in attr.l_states:
                # s.l_variable_values may be ints or '0'/'1' strings
                states.append(tuple(str(v) for v in s.l_variable_values))
            result.add(tuple(states))
    return result


def test_bruteforce_vs_sat_simple_identity():
    # Two variables that keep their own value -> each state is a fixed point
    ln = LocalNetwork(index=1, internal_variables=[1, 2])

    # Each internal variable function is identity on itself
    iv1 = InternalVariable(1, [[1]])
    iv2 = InternalVariable(2, [[2]])
    ln.descriptive_function_variables = [iv1, iv2]

    # No external signals
    ln.process_input_signals([])

    # Brute force
    bf = LocalNetwork.find_local_attractors_brute_force(ln)
    bf_set = _normalize_attractors(bf.local_scenes)

    # Reset scenes for SAT run (fresh object)
    ln2 = LocalNetwork(index=1, internal_variables=[1, 2])
    ln2.descriptive_function_variables = [iv1, iv2]
    ln2.process_input_signals([])
    sat = LocalNetwork.find_local_attractors(ln2)
    sat_set = _normalize_attractors(sat.local_scenes)

    assert bf_set == sat_set
