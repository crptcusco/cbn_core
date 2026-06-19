import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN  # noqa: E402
from cbnetwork.coupling import CouplingStrategy  # noqa: E402
from cbnetwork.coupling_bitmask import CouplingFactory  # noqa: E402


class BitmaskCouplingStrategy(CouplingStrategy):
    """
    Adapter to use CouplingFunction within the existing CBN generator.
    """

    def __init__(self, coupling_func):
        self.cf = coupling_func
        self.coupling_type = coupling_func.name
        self.bitmask = coupling_func.bitmask

    def generate_coupling_function(self, output_variables: list[int]) -> str:
        if self.cf.name == "OR":
            return " " + " ∨ ".join(map(str, output_variables)) + " "
        elif self.cf.name == "AND":
            return " " + " ∧ ".join(map(str, output_variables)) + " "
        elif self.cf.name == "BUFFER":
            return " " + str(output_variables[0]) + " "
        return " " + " ∨ ".join(map(str, output_variables)) + " "

    def to_cnf(
        self, output_variables: list[int], coupling_variable: int
    ) -> list[list[int]]:
        clauses = []
        for var in output_variables:
            clauses.append([-var, coupling_variable])
        clauses.append(output_variables + [-coupling_variable])
        return clauses


def main():
    parser = argparse.ArgumentParser(description="CBN Topology Generator")
    parser.add_argument("--topology", type=int, default=3, help="Topology type")
    parser.add_argument(
        "--networks", type=int, default=4, help="Number of local networks"
    )
    parser.add_argument("--vars", type=int, default=5, help="Variables per network")
    parser.add_argument("--output", type=str, required=False, help="Output JSON file")

    args = parser.parse_args()

    # Set default output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    if not args.output:
        output_path = (
            output_dir / f"topology_{args.topology}_n{args.networks}_v{args.vars}.json"
        )
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"[*] Generating CBN: Topology={args.topology}, Networks={args.networks}, Vars={args.vars}"
    )

    def get_dynamic_coupling(k):
        if k == 1:
            return BitmaskCouplingStrategy(CouplingFactory.create_buffer_function())
        else:
            import random

            choice = random.randint(0, 3)
            if choice == 0:
                return BitmaskCouplingStrategy(CouplingFactory.create_or_function(k))
            elif choice == 1:
                return BitmaskCouplingStrategy(CouplingFactory.create_and_function(k))
            elif choice == 2:
                return BitmaskCouplingStrategy(
                    CouplingFactory.create_majority_function(k)
                )
            else:
                return BitmaskCouplingStrategy(
                    CouplingFactory.create_mixed_random_function(k)
                )

    strat = get_dynamic_coupling(1)  # k is 1 for now

    cbn = CBN.cbn_generator(
        v_topology=args.topology,
        n_local_networks=args.networks,
        n_vars_network=args.vars,
        n_input_variables=1,
        n_output_variables=1,
        coupling_strategy=strat,
    )

    cbn.to_json(str(output_path))
    print(f"[OK] Saved to {output_path}")


if __name__ == "__main__":
    main()
