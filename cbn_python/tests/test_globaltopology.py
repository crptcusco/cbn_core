import matplotlib

# Use non-interactive backend for tests
matplotlib.use("Agg")
import pytest  # noqa: E402
from cbnetwork.globaltopology import GlobalTopology, NullTopology  # noqa: E402


def test_generate_sample_topology_valid_complete():
    o = GlobalTopology.generate_sample_topology(1, 3)
    # CompleteDigraph should have 3 nodes
    nodes = o.get_nodes()
    assert len(nodes) == 3
    edges = o.get_edges()
    assert isinstance(edges, list)


def test_null_topology():
    o = NullTopology()
    assert o.get_nodes() == []
    assert o.get_edges() == []


@pytest.mark.parametrize("v_topology", [1, 2, 3, 7, 9])
def test_generate_sample_topology_all_types(v_topology):
    o = GlobalTopology.generate_sample_topology(v_topology, 4)
    assert o is not None
