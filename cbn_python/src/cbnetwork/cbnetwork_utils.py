from typing import Any, Dict


def flatten(x):
    """Recursively flattens a nested list or tuple into a single sequence."""
    if isinstance(x, (list, tuple)):
        for item in x:
            yield from flatten(item)
    else:
        yield x


def _convert_to_tuple(x: Any) -> Any:
    """Recursively converts lists into tuples to make them hashable."""
    if isinstance(x, list):
        return tuple(_convert_to_tuple(item) for item in x)
    return x


def evaluate_pair(
    base_pairs: list, candidate_pair: tuple, d_local_attractors: Dict
) -> bool:
    """
    Checks whether a candidate pair is compatible with the base pairs.
    """

    def _flatten(x):
        if isinstance(x, (list, tuple)):
            for item in x:
                yield from _flatten(item)
        else:
            yield x

    base_attractor_indices = {x for pair in base_pairs for x in _flatten(pair)}
    already_visited_networks = {
        d_local_attractors[idx][0] for idx in base_attractor_indices
    }

    double_check = 0
    for candidate_idx in _flatten(candidate_pair):
        if d_local_attractors[candidate_idx][0] in already_visited_networks:
            if candidate_idx in base_attractor_indices:
                double_check += 1
        else:
            double_check += 1

    return double_check == 2


def cartesian_product_mod(
    base_pairs: list, candidate_pairs: list, d_local_attractors: Dict
) -> list:
    """Performs a modified Cartesian product between two lists of pairs, filtering incompatible combinations."""
    field_pair_list = []
    for base_pair in base_pairs:
        for candidate_pair in candidate_pairs:
            if isinstance(base_pair, tuple):
                base_pair = list(base_pair)

            if evaluate_pair(base_pair, candidate_pair, d_local_attractors):
                new_pair = base_pair + [candidate_pair]
                field_pair_list.append(new_pair)

    return field_pair_list


def process_single_base_pair(base_pair, candidate_pairs, d_local_attractors):
    """Processes a single base pair by applying `cartesian_product_mod`."""
    return cartesian_product_mod([base_pair], candidate_pairs, d_local_attractors)
