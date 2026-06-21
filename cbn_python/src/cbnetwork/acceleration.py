import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    logger.warning("Numba not found. Turbo acceleration will be disabled.")

if HAS_NUMBA:

    @njit
    def evaluate_field_pair_kernel(
        base_field_attractors,  # 1D array: attractor indices in current field
        base_field_networks,  # 1D array: network indices for each attractor in field
        candidate_pair,  # tuple: (attr_idx_1, attr_idx_2)
        attr_to_network,  # 1D array: mapping from attractor index to network index
    ):
        """
        Checks if a candidate pair is compatible with the current field.
        Returns 1 if compatible, 0 otherwise.
        """
        cand_attr_1, cand_attr_2 = candidate_pair
        cand_net_1 = attr_to_network[cand_attr_1]
        cand_net_2 = attr_to_network[cand_attr_2]

        # Track which networks are already in the field
        visited_networks = set(base_field_networks)

        double_check = 0

        # Check first attractor of candidate pair
        if cand_net_1 in visited_networks:
            # Network already visited - must use same attractor
            if cand_attr_1 in base_field_attractors:
                double_check += 1
        else:
            # New network - always compatible
            double_check += 1

        # Check second attractor of candidate pair
        if cand_net_2 in visited_networks:
            if cand_attr_2 in base_field_attractors:
                double_check += 1
        else:
            double_check += 1

        return 1 if double_check == 2 else 0

    @njit(parallel=True)
    def filter_compatible_pairs_kernel(
        base_fields,  # 2D array: (n_fields, max_field_size) - padded with -1
        base_field_sizes,  # 1D array: actual size of each field
        base_field_networks,  # 2D array: (n_fields, max_field_size) - network IDs
        candidate_pairs,  # 2D array: (n_pairs, 2) - candidate pairs to test
        attr_to_network,  # 1D array: mapping from attractor to network
    ):
        """
        Filters candidate pairs for compatibility with each base field.
        Returns a 2D boolean array: (n_fields, n_pairs)
        """
        n_fields = len(base_fields)
        n_pairs = len(candidate_pairs)

        compatible = np.zeros((n_fields, n_pairs), dtype=np.int8)

        for i in prange(n_fields):
            field_size = base_field_sizes[i]
            field_attrs = base_fields[i, :field_size]
            field_nets = base_field_networks[i, :field_size]

            for j in range(n_pairs):
                pair = candidate_pairs[j]

                # Manual implementation since we can't pass tuples to njit easily
                cand_attr_1 = pair[0]
                cand_attr_2 = pair[1]
                cand_net_1 = attr_to_network[cand_attr_1]
                cand_net_2 = attr_to_network[cand_attr_2]

                # Check if networks are in field
                net1_in_field = False
                net2_in_field = False
                attr1_in_field = False
                attr2_in_field = False

                for k in range(field_size):
                    if field_nets[k] == cand_net_1:
                        net1_in_field = True
                        if field_attrs[k] == cand_attr_1:
                            attr1_in_field = True
                    if field_nets[k] == cand_net_2:
                        net2_in_field = True
                        if field_attrs[k] == cand_attr_2:
                            attr2_in_field = True

                # Evaluate compatibility
                double_check = 0
                if net1_in_field:
                    if attr1_in_field:
                        double_check += 1
                else:
                    double_check += 1

                if net2_in_field:
                    if attr2_in_field:
                        double_check += 1
                else:
                    double_check += 1

                if double_check == 2:
                    compatible[i, j] = 1

        return compatible

else:

    def evaluate_field_pair_kernel(*args):
        raise ImportError("Numba is required for Turbo acceleration.")

    def filter_compatible_pairs_kernel(*args):
        raise ImportError("Numba is required for Turbo acceleration.")
