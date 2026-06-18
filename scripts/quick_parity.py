import json
import random
import subprocess
import sys
from pathlib import Path

N_SAMPLES = 10
TOPOLOGIES = [7, 9]
NETWORKS_RANGE = (3, 4)
VARS_RANGE = (2, 3)

ROOT_DIR = Path(__file__).resolve().parents[1]
CPP_BINARY = ROOT_DIR / "cbn_cpp" / "build" / "scientific_benchmarking"
PYTHON_GEN = ROOT_DIR / "experiments" / "mix" / "cbn_python_gen.py"
PYTHON_SOLVER = ROOT_DIR / "experiments" / "mix" / "cbn_python_solver.py"
TEMP_DIR = ROOT_DIR / "temp_parity"
TEMP_DIR.mkdir(exist_ok=True)


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


def main():
    success_count = 0
    for i in range(1, N_SAMPLES + 1):
        topo = random.choice(TOPOLOGIES)
        nets = random.randint(*NETWORKS_RANGE)
        vars = random.randint(*VARS_RANGE)
        topo_file = TEMP_DIR / f"quick_{i}.json"
        py_dyn = TEMP_DIR / f"quick_py_{i}.json"
        cpp_dyn = TEMP_DIR / f"quick_cpp_{i}.json"
        run_command(
            [
                sys.executable,
                str(PYTHON_GEN),
                "--topology",
                str(topo),
                "--networks",
                str(nets),
                "--vars",
                str(vars),
                "--output",
                str(topo_file),
            ]
        )
        run_command(
            [
                sys.executable,
                str(PYTHON_SOLVER),
                "--input",
                str(topo_file),
                "--output",
                str(py_dyn),
            ]
        )
        run_command(
            [
                str(CPP_BINARY),
                "--input",
                str(topo_file),
                "--dir",
                str(TEMP_DIR),
                "--samples",
                "1",
            ]
        )
        (TEMP_DIR / "cbn_sample_1_AdvancedParallel_dynamics.json").replace(cpp_dyn)

        with open(py_dyn) as f:
            py_data = json.load(f)["attractors"]
        with open(cpp_dyn) as f:
            cpp_data = json.load(f)["attractors"]

        if py_data == cpp_data:
            success_count += 1
            print(f"[{i}/{N_SAMPLES}] OK")
        else:
            print(f"[{i}/{N_SAMPLES}] FAIL")
            sys.exit(1)
    print(f"SUCCESS: {success_count}/{N_SAMPLES}")


if __name__ == "__main__":
    main()
