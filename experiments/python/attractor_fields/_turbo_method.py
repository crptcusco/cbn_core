    def mount_stable_attractor_fields_turbo(self) -> None:
        """
        Numba-accelerated version of Step 3: Mount Stable Attractor Fields.
        Uses numerical arrays and JIT-compiled kernels for faster field assembly.
        """
        from cbnetwork.acceleration import filter_compatible_pairs_kernel, HAS_NUMBA
        if not HAS_NUMBA:
            return self.mount_stable_attractor_fields()

        CustomText.make_title("FIND ATTRACTOR FIELDS (TURBO)")
        
        # Order edges by compatibility
        self.order_edges_by_compatibility()
        
        # Build attractor-to-network mapping
        max_attr_idx = max(self.d_local_attractors.keys())
        attr_to_network = np.zeros(max_attr_idx + 1, dtype=np.int32)
        for attr_idx, (net_idx, _) in self.d_local_attractors.items():
            attr_to_network[attr_idx] = net_idx
        
        # Initialize with first edge
        first_edge = self.l_directed_edges[0]
        base_pairs_list = (
            first_edge.d_comp_pairs_attractors_by_value[0] +
            first_edge.d_comp_pairs_attractors_by_value[1]
        )
        
        if not base_pairs_list:
            self.d_attractor_fields = {}
            CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS (TURBO)")
            return
        
        # Convert base pairs to numerical format
        # Each field is represented as a list of attractor indices
        current_fields = []
        for pair in base_pairs_list:
            current_fields.append(list(pair))
        
        # Process each remaining edge
        for edge_idx, o_directed_edge in enumerate(self.l_directed_edges[1:], start=1):
            candidate_pairs_list = (
                o_directed_edge.d_comp_pairs_attractors_by_value[0] +
                o_directed_edge.d_comp_pairs_attractors_by_value[1]
            )
            
            if not candidate_pairs_list or not current_fields:
                current_fields = []
                break
            
            # Prepare data for Numba kernel
            n_fields = len(current_fields)
            n_pairs = len(candidate_pairs_list)
            
            # Find max field size for padding
            max_field_size = max(len(f) for f in current_fields)
            
            # Create padded arrays
            fields_array = np.full((n_fields, max_field_size), -1, dtype=np.int32)
            field_sizes = np.zeros(n_fields, dtype=np.int32)
            field_networks = np.full((n_fields, max_field_size), -1, dtype=np.int32)
            
            for i, field in enumerate(current_fields):
                field_sizes[i] = len(field)
                for j, attr_idx in enumerate(field):
                    fields_array[i, j] = attr_idx
                    field_networks[i, j] = attr_to_network[attr_idx]
            
            # Candidate pairs array
            pairs_array = np.array(candidate_pairs_list, dtype=np.int32)
            
            # Call Numba kernel
            compatible_matrix = filter_compatible_pairs_kernel(
                fields_array,
                field_sizes,
                field_networks,
                pairs_array,
                attr_to_network
            )
            
            # Build new fields from compatibility matrix
            new_fields = []
            for i in range(n_fields):
                for j in range(n_pairs):
                    if compatible_matrix[i, j]:
                        # Combine field with pair
                        new_field = current_fields[i] + list(candidate_pairs_list[j])
                        new_fields.append(new_field)
            
            current_fields = new_fields
            
            if not current_fields:
                break
        
        # Generate final attractor fields dictionary
        self.d_attractor_fields = {}
        for i, field in enumerate(current_fields, start=1):
            # Remove duplicates and convert to list
            self.d_attractor_fields[i] = list(set(field))
        
        logging.getLogger(__name__).info(
            "END MOUNT ATTRACTOR FIELDS (TURBO) (Total fields: %d)", 
            len(self.d_attractor_fields)
        )
        CustomText.make_sub_sub_title("END MOUNT ATTRACTOR FIELDS (TURBO)")
