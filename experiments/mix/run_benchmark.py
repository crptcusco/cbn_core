import csv
import json
import random
import subprocess
import sys
from pathlib import Path

# ======================================================================
# CONFIGURACIÓN DEL EXPERIMENTO (SMOKE TEST MODE)
# ======================================================================
N_SAMPLES = 5  # Reducido a 5 para una validación rápida
NETWORKS = 6  # 6 redes locales
VARS = 5  # 5 variables por red (32 estados por subred)

# Topologías a incluir: Se fija en 2 para asegurar la cadena lineal unidireccional
# (IDs estándar: 1: complete, 2: linear/path, 3: cycle, 7: dorogovtsev_mendes, 9: scale_free)
TOPOLOGIES = [2]

MIX_DIR = Path(__file__).resolve().parent
ROOT_DIR = MIX_DIR.parents[1]
CPP_BINARY = ROOT_DIR / "cbn_cpp" / "build" / "scientific_benchmarking"
PYTHON_GEN = MIX_DIR / "cbn_python_gen.py"
PYTHON_SOLVER = MIX_DIR / "cbn_python_solver.py"
OUTPUT_DIR = MIX_DIR / "output"
OUTPUT_CSV = OUTPUT_DIR / "final_comparative_benchmark.csv"

OUTPUT_DIR.mkdir(exist_ok=True)


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr
    return True, result.stdout


def compare_dynamics(py_root, cpp_root):
    def get_canonical_fields(root_data):
        exec_data = root_data.get("pipeline_execution", {})
        step3 = exec_data.get("step_3_global_fields", {})
        fields = step3.get("attractor_fields", [])
        return sorted([tuple(sorted(f["attractor_indices"])) for f in fields])

    py_canonical = get_canonical_fields(py_root)
    cpp_canonical = get_canonical_fields(cpp_root)

    if py_canonical == cpp_canonical:
        return True, len(py_canonical)
    else:
        return False, (py_canonical, cpp_canonical)


def main():
    print("=== CBN HYBRID BENCHMARK ORCHESTRATOR (SMOKE TEST) ===")
    print(f"Output directory: {OUTPUT_DIR}")

    if not CPP_BINARY.exists():
        print(f"[Error] C++ Binary not found at {CPP_BINARY}.")
        return

    with open(OUTPUT_CSV, mode="w", newline="") as csv_file:
        fieldnames = [
            "sample_id",
            "topology",
            "py_time_ms",
            "cpp_time_ms",
            "speedup",
            "status",
            "fields",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, N_SAMPLES + 1):
            topo = random.choice(TOPOLOGIES)
            print(f"\n[*] Sample {i}/{N_SAMPLES} | Topology (Linear): {topo}")

            topo_file = OUTPUT_DIR / f"cbn_sample_{i}_topology.json"
            py_dyn_file = OUTPUT_DIR / f"py_sample_{i}_dynamics.json"
            cpp_dyn_file = OUTPUT_DIR / f"cpp_sample_{i}_dynamics.json"

            # 1. Generate
            success, out = run_command(
                [
                    sys.executable,
                    str(PYTHON_GEN),
                    "--topology",
                    str(topo),
                    "--networks",
                    str(NETWORKS),
                    "--vars",
                    str(VARS),
                    "--output",
                    str(topo_file),
                ]
            )
            if not success:
                break

            # 2. Python Solve
            success, out = run_command(
                [
                    sys.executable,
                    str(PYTHON_SOLVER),
                    "--input",
                    str(topo_file),
                    "--output",
                    str(py_dyn_file),
                ]
            )
            if not success:
                break

            with open(py_dyn_file) as f:
                py_res = json.load(f)
                py_time = py_res["performance"]["total_ms"]

            # 3. C++ Solve
            success, out = run_command(
                [
                    str(CPP_BINARY),
                    "--samples",
                    "1",
                    "--input",
                    str(topo_file),
                    "--dir",
                    str(OUTPUT_DIR),
                ]
            )
            if not success:
                writer.writerow(
                    {"sample_id": i, "topology": topo, "status": "CPP_CRASH"}
                )
                continue

            cpp_gen_file = OUTPUT_DIR / "cbn_sample_1_AdvancedParallel_dynamics.json"
            if cpp_gen_file.exists():
                cpp_gen_file.replace(cpp_dyn_file)
            else:
                break

            with open(cpp_dyn_file) as f:
                cpp_res = json.load(f)
                # Performance moved to "performance" (wait, I used "performance" in C++ or "metrics"?)
                # Looking at my cat for scientific_benchmarking.cpp: j_out["performance"] = { ... }
                cpp_time = cpp_res["performance"]["total_ms"]

            # 4. Compare
            is_equal, result = compare_dynamics(py_res, cpp_res)

            if is_equal:
                speedup = py_time / cpp_time if cpp_time > 0 else 0
                print(f"[OK] Parity match! Fields: {result}")
                writer.writerow(
                    {
                        "sample_id": i,
                        "topology": topo,
                        "py_time_ms": py_time,
                        "cpp_time_ms": cpp_time,
                        "speedup": speedup,
                        "status": "SUCCESS",
                        "fields": result,
                    }
                )
            else:
                print(f"🚨 [ERROR] PARITY DIVERGENCE in sample {i}!")
                writer.writerow(
                    {"sample_id": i, "topology": topo, "status": "PARITY_ERROR"}
                )
                break

            csv_file.flush()

    print(f"\n[DONE] Benchmark report saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
