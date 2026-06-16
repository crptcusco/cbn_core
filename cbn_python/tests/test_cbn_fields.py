from cbnetwork.cbnetwork import CBN


class DummyLocalNetwork:
    def __init__(self, index):
        self.index = index
        self.output_signals = []


class DummyEdge:
    def __init__(self, idx, inp, out, comp_pairs=None):
        self.index = idx
        self.input_local_network = inp
        self.output_local_network = out
        # comp_pairs expected as dict {0: [...], 1: [...]}
        self.d_comp_pairs_attractors_by_value = comp_pairs or {0: [], 1: []}


def edge_grade(edge, network_degrees):
    return network_degrees.get(edge.input_local_network, 0) + network_degrees.get(
        edge.output_local_network, 0
    )


def test_order_edges_by_grade_sorts_by_degree():
    nets = [DummyLocalNetwork(i) for i in range(1, 4)]
    # Create edges such that two edges have higher combined degree
    e1 = DummyEdge(1, 1, 2)
    e2 = DummyEdge(2, 1, 2)
    e3 = DummyEdge(3, 2, 3)
    cbn = CBN(l_local_networks=nets, l_directed_edges=[e1, e2, e3])

    # compute degrees as method would
    network_degrees = {net.index: 0 for net in cbn.l_local_networks}
    for edge in cbn.l_directed_edges:
        network_degrees[edge.input_local_network] += 1
        network_degrees[edge.output_local_network] += 1

    cbn.order_edges_by_grade()
    first_grade = edge_grade(cbn.l_directed_edges[0], network_degrees)
    # ensure first grade is the maximum among edges
    grades = [edge_grade(e, network_degrees) for e in cbn.l_directed_edges]
    assert first_grade == max(grades)


def test_mount_stable_attractor_fields_basic_combination():
    # Local nets 1..3
    nets = [DummyLocalNetwork(i) for i in range(1, 4)]

    # Edge 0 has pair (1,2), edge 1 has candidate (2,3)
    e0 = DummyEdge(0, 1, 2, comp_pairs={0: [(1, 2)], 1: []})
    e1 = DummyEdge(1, 2, 3, comp_pairs={0: [(2, 3)], 1: []})

    cbn = CBN(l_local_networks=nets, l_directed_edges=[e0, e1])

    # d_local_attractors mapping: index -> (local_network_index, dummy)
    cbn.d_local_attractors = {
        1: (1, None),
        2: (2, None),
        3: (3, None),
    }

    # Run the mounting algorithm
    cbn.mount_stable_attractor_fields()

    # After mounting, expect at least one attractor field containing 1,2,3
    found = False
    for field in cbn.d_attractor_fields.values():
        if set(field) >= {1, 2, 3}:
            found = True
            break
    assert (
        found
    ), f"Expected an attractor field containing 1,2,3, got {cbn.d_attractor_fields}"
