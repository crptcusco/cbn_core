from cbnetwork.internalvariable import InternalVariable
from cbnetwork.localnetwork import LocalNetwork


def test_local_network_brute_force_attractors():
    # Setup a simple 2-variable network:
    # v1(t+1) = v2(t)
    # v2(t+1) = v1(t)
    # States: (0,0)->(0,0) [Attractor], (1,1)->(1,1) [Attractor], (0,1)->(1,0)->(0,1) [Cycle Attractor]

    net = LocalNetwork(index=1, internal_variables=[1, 2])
    var1 = InternalVariable(index=1, cnf_function=[[2]])
    var2 = InternalVariable(index=2, cnf_function=[[1]])
    net.descriptive_function_variables = [var1, var2]
    net.process_input_signals([])

    LocalNetwork.find_local_attractors_brute_force(net)

    assert net.attractor_count == 3
    # Attractors: [(0,0)], [(1,1)], [(0,1), (1,0)]
    attractor_lengths = sorted(
        [len(a.l_states) for a in net.local_scenes[0].l_attractors]
    )
    assert attractor_lengths == [1, 1, 2]


def test_local_network_with_coupling():
    # v1(t+1) = external_v10
    net = LocalNetwork(index=1, internal_variables=[1])
    var1 = InternalVariable(index=1, cnf_function=[[10]])
    net.descriptive_function_variables = [var1]

    mock_signal = type("obj", (object,), {"index_variable": 10})
    net.process_input_signals([mock_signal])

    assert net.external_variables == [10]
    assert net.total_variables == [1, 10]

    # Test brute force with scenes
    # scene '0': v10=0 -> v1(t+1)=0. Attractor [(0)]
    # scene '1': v10=1 -> v1(t+1)=1. Attractor [(1)]
    LocalNetwork.find_local_attractors_brute_force(net, local_scenes=["0", "1"])
    assert net.attractor_count == 2
    assert len(net.local_scenes) == 2
    # In my current implementation of LocalState inside brute force, l_variable_values is a list of integers
    assert net.local_scenes[0].l_attractors[0].l_states[0].l_variable_values == [0, 0]
    assert net.local_scenes[1].l_attractors[0].l_states[0].l_variable_values == [1, 1]
