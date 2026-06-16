import matplotlib

# Use non-interactive backend for tests
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cbnetwork.globaltopology import GlobalTopology, NullTopology


def test_generate_sample_topology_valid_complete():
    o = GlobalTopology.generate_sample_topology(1, 3)
    # CompleteDigraph should have 3 nodes
    nodes = o.get_nodes()
    assert len(nodes) == 3
    edges = o.get_edges()
    assert isinstance(edges, list)


import pytest

def test_generate_sample_topology_invalid_topology_raises_error():
    """
    Tests that providing an invalid topology ID to the generator
    correctly raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid topology option: 999"):
        GlobalTopology.generate_sample_topology(999, 4)


def test_plot_topology_on_empty_nulltopology_and_nonempty():
    # Explicit NullTopology
    n = NullTopology(message="Empty topology test")
    fig, ax = plt.subplots()
    n.plot_topology(ax=ax)
    assert any("Empty topology test" in t.get_text() for t in ax.texts)

    # Non-empty graph should not show the empty message
    o = GlobalTopology.generate_sample_topology(1, 4)
    fig2, ax2 = plt.subplots()
    o.plot_topology(ax=ax2)
    # Ensure no text contains the word 'Empty' which would indicate a null message
    assert all("Empty" not in t.get_text() for t in ax2.texts)
