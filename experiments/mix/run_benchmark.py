import csv
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

# ======================================================================
# CONFIGURACIÓN DEL EXPERIMENTO (SMOKE TEST MODE)
# ======================================================================
N_SAMPLES = 5   # Reducido a 5 para una validación rápida
NETWORKS = 6    # 6 redes locales
VARS = 5        # 5 variables por red (32 estados por subred)

# Topologías a incluir: Se fija en 2 para asegurar la cadena lineal unidireccional
# (IDs estándar: 1: complete, 2: linear/path, 3: cycle, 7: dorogovtsev_mendes, 9: scale_free)
TOPOLOGIES = [2] 

MIX_DIR = Path(__file__).resolve().parent
ROOT_DIR = MIX_DIR.parents[1]
CPP_BINARY = ROOT_DIR / "cbn_cpp" / "build" / "scientific_benchmarking"
PYTHON_GEN = MIX_DIR / "cbn_python_gen.py"
PYTHON_SOLVER = MIX_DIR / "cbn_python_solver.py"
OUTPUT_CSV = MIX_DIR / "final_comparative_benchmark.csv"


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False, result.stderr
    return True, result.stdout


def compare_dynamics(py_file, cpp_file):
    if not os.path.exists(py_file) or not os.path.exists(cpp_file):
        return False, "Missing files"
    with open(py_file) as f:
        py_data = json.load(f)
    with open(cpp_file) as f:
        cpp_data = json.load(f)

    def get_canonical_attractors(data):
        attractors = data.get("attractors", [])
        # Cada atractor tiene 'states' que es una lista ordenada de enteros
        return sorted(
            [tuple(sorted([int(s) for s in a["states"]])) for a in attractors]
        )

    py_canonical = get_canonical_attractors(py_data)
    cpp_canonical = get_canonical_attractors(cpp_data)

    if py_canonical == cpp_canonical:
        return True, len(py_canonical)
    else:
        return False, (py_canonical, cpp_canonical)


def clean_old_files(sample_id):
    files = [
        MIX_DIR / f"cbn_sample_{sample_id}_topology.json",
        MIX_DIR / f"py_sample_{sample_id}_dynamics.json",
        MIX_DIR / f"cpp_sample_{sample_id}_dynamics.json",
        MIX_DIR / "cbn_sample_1_AdvancedParallel_dynamics.json",
        MIX_DIR / "temp_bench.csv",
    ]
    for f in files:
        if f.exists():
            os.remove(f)


def main():
    print("=== CBN HYBRID BENCHMARK ORCHESTRATOR (SMOKE TEST) ===")
    print(f"Root: {ROOT_DIR}")
    print(f"Binary: {CPP_BINARY}")
    print(f"Config: {NETWORKS} networks x {VARS} variables | Lineal Topology")
    print("=" * 60)

    if not CPP_BINARY.exists():
        print(f"[Error] C++ Binary not found at {CPP_BINARY}. Please compile first.")
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

            clean_old_files(i)

            topo_file = MIX_DIR / f"cbn_sample_{i}_topology.json"
            py_dyn_file = MIX_DIR / f"py_sample_{i}_dynamics.json"
            cpp_dyn_file = MIX_DIR / f"cpp_sample_{i}_dynamics.json"

            # 1. Generar la red sintética lineal pequeña
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

            # 2. Ejecutar el Solver de Python verificado (Pipeline limpio sin Fuerza Bruta)
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

            # 3. Ejecutar el Solver de C++
            success, out = run_command(
                [
                    str(CPP_BINARY),
                    "--samples",
                    "1",
                    "--input",
                    str(topo_file),
                    "--dir",
                    str(MIX_DIR),
                    "--output",
                    str(MIX_DIR / "temp_bench.csv"),
                ]
            )
            if not success:
                print(f"[FAIL] C++ Solver crashed on sample {i}")
                writer.writerow(
                    {"sample_id": i, "topology": topo, "status": "CPP_CRASH"}
                )
                continue

            # Capturar y renombrar la salida hardcodeada de C++ para la muestra actual
            cpp_gen_file = MIX_DIR / "cbn_sample_1_AdvancedParallel_dynamics.json"
            if cpp_gen_file.exists():
                os.rename(cpp_gen_file, cpp_dyn_file)
            else:
                print(f"[Error] C++ didn't produce dynamics file. Output: {out}")
                break

            with open(cpp_dyn_file) as f:
                cpp_res = json.load(f)
                cpp_time = cpp_res["performance"]["total_ms"]

            # 4. Control de calidad: Verificación canónica de paridad científica
            is_equal, result = compare_dynamics(py_dyn_file, cpp_dyn_file)

            if is_equal:
                speedup = py_time / cpp_time if cpp_time > 0 else 0
                print(
                    f"[OK] Parity match! Fields: {result} | Py: {py_time:.2f}ms | Cpp: {cpp_time:.2f}ms | Speedup: {speedup:.2f}x"
                )
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
                if isinstance(result, tuple):
                    print(f"   -> Python attractor fields found: {len(result[0])}")
                    print(f"   -> C++ attractor fields found: {len(result[1])}")
                else:
                    print(f"   -> Error detail: {result}")
                writer.writerow(
                    {"sample_id": i, "topology": topo, "status": "PARITY_ERROR"}
                )
                break

            csv_file.flush()

    print(f"\n[DONE] Benchmark report saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()