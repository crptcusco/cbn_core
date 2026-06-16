import os
from cbnetwork.localnetwork import LocalNetwork
from cbnetwork.internalvariable import InternalVariable


def extract_attractor_signatures(local_network):
    sigs = []
    for scene in local_network.local_scenes:
        scene_sigs = []
        for attr in scene.l_attractors:
            # Normalize values to ints for apples-to-apples comparison
            states = tuple(
                tuple(int(v) for v in s.l_variable_values) for s in attr.l_states
            )
            # Canonicalize cycle by rotation so lexicographically smallest state comes first
            if len(states) > 1:
                rotations = [tuple(states[i:] + states[:i]) for i in range(len(states))]
                states = min(rotations)
            scene_sigs.append(states)
        sigs.append(tuple(sorted(scene_sigs)))
    return tuple(sigs)


def build_cycle_network():
    net = LocalNetwork(index=1, internal_variables=[1, 2])
    # var1 = not 2  -> CNF: [[-2]]
    # var2 = var1    -> CNF: [[1]]
    var1 = InternalVariable(index=1, cnf_function=[[-2]])
    var2 = InternalVariable(index=2, cnf_function=[[1]])
    net.descriptive_function_variables = [var1, var2]
    return net


def build_fixed_network():
    net = LocalNetwork(index=2, internal_variables=[1])
    # Identity: var1_next = var1 -> CNF [[1]]
    var1 = InternalVariable(index=1, cnf_function=[[1]])
    net.descriptive_function_variables = [var1]
    return net


def compare_by_build(net_builder):
    a = net_builder()
    b = net_builder()
    # Ensure total variables bookkeeping required by SAT-based routines
    for net in (a, b):
        net.total_variables = net.internal_variables.copy()
        net.total_variables_count = len(net.total_variables)
        net.cnf_variables_map = {}
    LocalNetwork.find_local_attractors_brute_force(a)
    LocalNetwork.find_local_attractors(b)
    return extract_attractor_signatures(a) == extract_attractor_signatures(b)


def test_cycle_network_agreement():
    assert compare_by_build(build_cycle_network)


def test_fixed_network_agreement():
    assert compare_by_build(build_fixed_network)
