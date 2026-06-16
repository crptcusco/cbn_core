import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN


def main():
    parser = argparse.ArgumentParser(description="CBN Python Solver")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument(
        "--output", type=str, required=True, help="Output dynamics JSON file"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[Error] Input file {args.input} not found.")
        sys.exit(1)

    cbn = CBN.from_json(args.input)

    start_time = time.perf_counter()

    # Use Brute Force for consistency with C++
    print("[*] Using Brute Force mode")
    cbn.find_local_attractors_brute_force_sequential()
    cbn.find_compatible_pairs()
    cbn.mount_stable_attractor_fields()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    dynamics = {
        "simulation_info": {
            "nodes": len(cbn.l_local_networks),
            "v_elements": len(cbn.l_local_networks) * cbn.get_n_local_variables(),
        },
        "attractors": [],
        "performance": {"total_ms": duration_ms},
    }

    for field_id, attractor_indices in cbn.d_attractor_fields.items():
        clean_indices = [int(idx) for idx in attractor_indices]
        dynamics["attractors"].append(
            {
                "id": int(field_id),
                "length": len(clean_indices),
                "states": sorted(clean_indices),
            }
        )

    with open(args.output, "w") as f:
        json.dump(dynamics, f, indent=4)

    print(
        f"[OK] Python simulation completed in {duration_ms:.2f} ms. Results saved to {args.output}"
    )


if __name__ == "__main__":
    main()
