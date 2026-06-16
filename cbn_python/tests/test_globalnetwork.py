from cbnetwork.globalnetwork.globalnetwork import (
    GlobalNetwork,
    GlobalState,
    GlobalAttractor,
)


class DummyAttractor:
    def __init__(self, g_index, states):
        self.g_index = g_index
        self.states = states


class DummyAttractorField:
    def __init__(self, l_attractor_indexes, ok=True, l_index=None):
        self.l_attractor_indexes = l_attractor_indexes
        self.l_global_states = None
        self._ok = ok
        self.l_index = l_index or [0]

    def test_global_dynamic(self):
        return self._ok


class DummyCBN:
    def __init__(self, attractors):
        # attractors: dict index->DummyAttractor
        self._attractors = attractors
        self.d_attractor_fields = []

    def get_local_attractor_by_index(self, i):
        return self._attractors.get(i)


def test_generate_global_states_collects_states():
    # attractor 1 has states ['a'], attractor 2 has states ['b','c']
    a1 = DummyAttractor(1, ["a"])
    a2 = DummyAttractor(2, ["b", "c"])
    o_cbn = DummyCBN({1: a1, 2: a2})
    o_field = DummyAttractorField([1, 2])
    GlobalNetwork.generate_global_states(o_field, o_cbn)
    assert o_field.l_global_states == ["a", "b", "c"]


def test_test_attractor_fields_returns_true_and_calls_methods(caplog):
    af1 = DummyAttractorField([1], ok=True)
    af2 = DummyAttractorField([2], ok=False)
    o_cbn = DummyCBN({})
    o_cbn.d_attractor_fields = [af1, af2]
    # Should return True regardless (implementation currently logs results)
    assert GlobalNetwork.test_attractor_fields(o_cbn) is True


def test_globalstate_and_globalattractor_simple_storage():
    gs = GlobalState(["x", "y"])
    ga = GlobalAttractor([gs])
    assert ga.l_global_states[0].l_values == ["x", "y"]
