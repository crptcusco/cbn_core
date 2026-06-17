import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "cbn_python" / "src"))

import traceback  # noqa: E402

from cbnetwork.cbnetwork import CBN  # noqa: E402


def run_audit(input_path: str):
    """
    Performs a comprehensive health check of the solver methods.
    """
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.", flush=True)
        return

    results = []
    detailed_logs = []  # Búfer en memoria para evitar que Numba/Hilos pisen los prints

    # 1. Attractor Finding Methods (Ya sin fuerza bruta)
    attractor_methods = [
        "find_local_attractors_sequential",
        "find_local_attractors_parallel",
        "find_local_attractors_parallel_with_weights",
    ]

    # 2. Compatible Pairs Methods
    pairs_methods = [
        "find_compatible_pairs",
        "find_compatible_pairs_parallel",
        "find_compatible_pairs_turbo",
        "find_compatible_pairs_parallel_with_weights",
    ]

    # 3. Attractor Field Methods
    field_methods = [
        "mount_stable_attractor_fields",
        "mount_stable_attractor_fields_turbo",
        "mount_stable_attractor_fields_parallel",
        "mount_stable_attractor_fields_parallel_chunks",
    ]

    def run_method(cbn, method_name, *args, **kwargs):
        method = getattr(cbn, method_name, None)
        if not method:
            return "MISSING", "Method not found", 0, 0

        start_time = time.perf_counter()
        try:
            method(*args, **kwargs)
            duration = time.perf_counter() - start_time

            count = 0
            if "attractor" in method_name and "field" not in method_name:
                count = cbn.get_n_local_attractors()
            elif "pair" in method_name:
                count = cbn.get_n_pair_attractors()
            elif "field" in method_name:
                count = cbn.get_n_attractor_fields()

            if count == 0 and "find" in method_name:
                return (
                    "OK",
                    f"Tiempo: {duration:.2f}s | Conteo: {count} (⚠️ WARNING: Empty results)",
                    duration,
                    count,
                )

            return (
                "OK",
                f"Tiempo: {duration:.2f}s | Conteo: {count}",
                duration,
                count,
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            err_msg = str(e)
            stack = traceback.extract_tb(sys.exc_info()[2])
            last_call = stack[-1] if stack else None
            loc = (
                f"({last_call.filename.split('/')[-1]}, Line {last_call.lineno})"
                if last_call
                else ""
            )
            return (
                "FAIL",
                f"ERROR: {type(e).__name__}: {err_msg} {loc}",
                duration,
                0,
            )

    # --- EJECUCIÓN SILENCIOSA (Acumulando datos) ---

    # Audit Attractor Methods
    for m in attractor_methods:
        cbn = CBN.from_json(input_path)
        status, msg, duration, count = run_method(cbn, m)
        results.append((m, status, msg, count))
        detailed_logs.append((f"[{status:4}] {m:45} -> {msg}", "ATTRACTORS"))

    # For Pairs and Fields, use a base CBN that worked
    base_cbn = CBN.from_json(input_path)
    base_cbn.find_local_attractors_sequential()

    for m in pairs_methods:
        for edge in base_cbn.l_directed_edges:
            edge.d_comp_pairs_attractors_by_value = {0: [], 1: []}

        status, msg, duration, count = run_method(base_cbn, m)
        results.append((m, status, msg, count))
        detailed_logs.append((f"[{status:4}] {m:45} -> {msg}", "PAIRS"))

    # Ensure we have pairs for field calculation
    base_cbn.find_compatible_pairs()

    for m in field_methods:
        base_cbn.d_attractor_fields = {}
        status, msg, duration, count = run_method(base_cbn, m)
        results.append((m, status, msg, count))
        detailed_logs.append((f"[{status:4}] {m:45} -> {msg}", "FIELDS"))

    # --- IMPRESIÓN DEL REPORTE UNIFICADO (Al final de todo) ---

    print("\n" + "=" * 70, flush=True)
    print("📊 REPORTE DE AUDITORÍA DE MÉTODOS DEL SOLVER - CBN_CORE", flush=True)
    print("=" * 70, flush=True)

    current_section = "ATTRACTORS"
    for log_line, section in detailed_logs:
        if section != current_section:
            print("-" * 70, flush=True)
            current_section = section
        print(log_line, flush=True)

    print("=" * 70, flush=True)
    print("🔍 VERIFICACIÓN DE PARIDAD CIENTÍFICA", flush=True)
    print("=" * 70, flush=True)

    def check_parity(group_name, methods_in_group):
        group_results = [
            r
            for r in results
            if r[0] in methods_in_group and r[1] == "OK" and r[3] > 0
        ]
        if not group_results:
            print(
                f"[WARN] No successful methods in group {group_name} to compare.",
                flush=True,
            )
            return

        counts = [r[3] for r in group_results]
        if len(set(counts)) > 1:
            print(f"🚨 ALERT: Divergence in {group_name}!", flush=True)
            for name, status, msg, count in group_results:
                print(f"   - {name}: {count}", flush=True)
        else:
            print(
                f"[OK] Parity maintained for {group_name} ({counts[0]} consistent results)",
                flush=True,
            )

    check_parity("Attractors", attractor_methods)
    check_parity("Compatible Pairs", pairs_methods)
    check_parity("Attractor Fields", field_methods)
    print("======================================================================\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="CBN Python Solver")
    parser.add_argument("--input", type=str, required=True, help="Input JSON file")
    parser.add_argument(
        "--output", type=str, required=False, help="Output dynamics JSON file"
    )
    parser.add_argument(
        "--audit", action="store_true", help="Run diagnostic audit"
    )

    args = parser.parse_args()

    if args.audit:
        run_audit(args.input)
        return

    if not args.output:
        print("[Error] --output is required when not in --audit mode.")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"[Error] Input file {args.input} not found.")
        sys.exit(1)

    cbn = CBN.from_json(args.input)

    start_time = time.perf_counter()

    # Consolidado: Usamos los métodos estables validados por la auditoría de paridad
    print("[*] Running standard pipeline (Validation Parity Verified)...")
    cbn.find_local_attractors_sequential()
    cbn.find_compatible_pairs()
    cbn.mount_stable_attractor_fields_turbo()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    dynamics = {
        "simulation_info": {
            "nodes": len(cbn.l_local_networks),
            "v_elements": len(cbn.l_local_networks)
            * cbn.get_n_local_variables(),
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