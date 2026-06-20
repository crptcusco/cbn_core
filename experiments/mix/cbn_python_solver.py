import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN  # noqa: E402
from cbnetwork.globaltopology import GlobalTopology  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="CBN Python Solver")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument(
        "--output", type=str, required=False, help="Output dynamics JSON file"
    )
    parser.add_argument(
        "--debug-dump", action="store_true", help="Dump detailed internal state"
    )

    args = parser.parse_args()

    # Set default output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if not args.output:
        input_stem = Path(args.input).stem
        output_path = output_dir / f"{input_stem}_dynamics.json"
    else:
        # If output is absolute or relative path, ensure directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(args.input):
        print(f"[Error] Input file {args.input} not found.")
        sys.exit(1)

    cbn = CBN.from_json(args.input)

    start_time = time.perf_counter()

    # Step 1: Local Attractors
    s1_start = time.perf_counter()
    cbn.find_local_attractors_sequential(use_brute_force=True)
    s1_ms = (time.perf_counter() - s1_start) * 1000

    # Step 2: Compatible Pairs
    s2_start = time.perf_counter()
    cbn.find_compatible_pairs()
    s2_ms = (time.perf_counter() - s2_start) * 1000

    # Step 3: Global Fields
    s3_start = time.perf_counter()
    cbn.mount_stable_attractor_fields_turbo()
    s3_ms = (time.perf_counter() - s3_start) * 1000

    end_time = time.perf_counter()
    total_ms = (end_time - start_time) * 1000

    # Metadata
    topo_type = "N/A"
    if cbn.o_global_topology:
        topo_type = GlobalTopology.allowed_topologies.get(
            cbn.o_global_topology.v_topology, "Unknown"
        )

    output_object = {
        "topology_metadata": {
            "topology_type": topo_type,
            "topology_id": Path(args.input).stem,
            "nodes": len(cbn.l_local_networks),
            "v_elements": len(cbn.l_local_networks) * cbn.get_n_local_variables(),
        },
        "pipeline_execution": {
            "step_1_local_attractors": [],
            "step_2_compatible_pairs": [],
            "step_3_global_fields": {
                "global_scenario": "N/A",
                "attractor_fields": [],
            },
        },
        "performance": {
            "step_1_ms": s1_ms,
            "step_2_ms": s2_ms,
            "step_3_ms": s3_ms,
            "total_ms": total_ms,
        },
    }

    # Populate Step 1: Local Attractors (Unpacked)
    for net in cbn.l_local_networks:
        for scene in net.local_scenes:
            # l_values can be a list or None. If list, its first element is the scene string.
            scenario_str = ""
            if scene.l_values and len(scene.l_values) > 0:
                scenario_str = scene.l_values[0]

            net_scene = {
                "network_id": net.index,
                "applied_function": "Logic_CNF",
                "local_scenario": [int(c) for c in scenario_str],
                "attractors": [],
            }
            for attr in scene.l_attractors:
                attr_data = {
                    "attractor_id": attr.l_index,
                    "global_id": attr.g_index,
                    "length": len(attr.l_states),
                    "states_unpacked": [],
                }
                for state in attr.l_states:
                    vals = state.l_variable_values
                    if isinstance(vals, str):
                        vals = [int(c) for c in vals]

                    unpacked = {}
                    for i, v_idx in enumerate(net.internal_variables):
                        unpacked[f"var_{v_idx}"] = int(vals[i])
                    attr_data["states_unpacked"].append(unpacked)
                net_scene["attractors"].append(attr_data)
            output_object["pipeline_execution"]["step_1_local_attractors"].append(
                net_scene
            )

    # Populate Step 2: Compatible Pairs
    for edge in cbn.l_directed_edges:
        for val in [0, 1]:
            pairs = edge.d_comp_pairs_attractors_by_value.get(val, [])
            for p in pairs:
                output_object["pipeline_execution"]["step_2_compatible_pairs"].append(
                    {
                        "source_network": edge.output_local_network,
                        "target_network": edge.input_local_network,
                        "source_attractor_id": p[0],
                        "target_attractor_id": p[1],
                        "coupling_value": val,
                        "is_compatible": True,
                    }
                )

    # Populate Step 3: Global Fields
    for field_id, attractor_indices in cbn.d_attractor_fields.items():
        field_data = {
            "field_id": int(field_id),
            "attractor_indices": [int(idx) for idx in attractor_indices],
            "global_state_unpacked": [],
        }

        global_state = {}
        for g_idx in attractor_indices:
            attr = cbn.get_local_attractor_by_index(g_idx)
            if attr and attr.l_states:
                net = cbn.get_network_by_index(attr.network_index)
                vals = attr.l_states[0].l_variable_values
                if isinstance(vals, str):
                    vals = [int(c) for c in vals]
                for i, v_idx in enumerate(net.internal_variables):
                    global_state[f"var_{v_idx}"] = int(vals[i])

        sorted_state = {
            k: global_state[k]
            for k in sorted(global_state.keys(), key=lambda x: int(x.split("_")[1]))
        }
        field_data["global_state_unpacked"].append(sorted_state)
        output_object["pipeline_execution"]["step_3_global_fields"][
            "attractor_fields"
        ].append(field_data)

    with open(output_path, "w") as f:
        json.dump(output_object, f, indent=4)

    print(
        f"[OK] Python simulation completed in {total_ms:.2f} ms. Results saved to {output_path}"
    )


if __name__ == "__main__":
    main()
