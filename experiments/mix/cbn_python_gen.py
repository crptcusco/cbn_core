import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN
from cbnetwork.coupling import OrCoupling

def main():
    parser = argparse.ArgumentParser(description='CBN Topology Generator')
    parser.add_argument('--topology', type=int, default=3, help='Topology type')
    parser.add_argument('--networks', type=int, default=4, help='Number of local networks')
    parser.add_argument('--vars', type=int, default=5, help='Variables per network')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file')

    args = parser.parse_args()

    print(f"[*] Generating CBN: Topology={args.topology}, Networks={args.networks}, Vars={args.vars}")

    cbn = CBN.cbn_generator(
        v_topology=args.topology,
        n_local_networks=args.networks,
        n_vars_network=args.vars,
        n_input_variables=1,
        n_output_variables=1,
        coupling_strategy=OrCoupling()
    )

    cbn.to_json(args.output)
    print(f"[OK] Saved to {args.output}")

if __name__ == "__main__":
    main()
