import argparse
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

# Corregido: Sube 3 niveles desde 'experiments/python' hasta la raíz 'cbn_core'
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN
from cbnetwork.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def validate_config(config: Dict[str, Any]) -> bool:
    """Basic validation of the configuration object."""
    required_keys = ["n_networks", "v_topology", "n_var_network"]
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration key: {key}")
            return False
    return True

def run_pipeline(config: Dict[str, Any], experiment_name: str, output_base: Path) -> Dict[str, Any]:
    """Executes the full CBN analysis pipeline for a single configuration and returns its summary."""
    exp_dir = output_base / experiment_name
    exp_dir.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "experiment_name": experiment_name,
        "config": config,
        "status": "STARTED",
        "performance": {},
        "results": {}
    }

    t_start = time.perf_counter()

    try:
        # Step 0: Generation
        logger.info(f"[{experiment_name}] Step 0: Generating CBN...")
        t_gen_start = time.perf_counter()
        cbn = CBN.generate_from_config(config)
        summary["performance"]["t_gen"] = time.perf_counter() - t_gen_start

        # Save topology immediately for traceability
        cbn.to_json(str(exp_dir / "topology.json"))

        # Step 1: Local Attractors
        logger.info(f"[{experiment_name}] Step 1: Finding local attractors...")
        t1_start = time.perf_counter()
        cbn.find_attractors_brute_force()
        summary["performance"]["t_p1"] = time.perf_counter() - t1_start
        summary["results"]["n_local_attractors"] = cbn.get_n_local_attractors()
        with open(exp_dir / "attractors.json", "w") as f:
            json.dump(cbn.to_json_attractors(), f, indent=4)

        # Step 2: Compatible Pairs
        logger.info(f"[{experiment_name}] Step 2: Finding compatible pairs...")
        t2_start = time.perf_counter()
        cbn.find_compatible_pairs()
        summary["performance"]["t_p2"] = time.perf_counter() - t2_start
        summary["results"]["n_pairs"] = cbn.get_n_pair_attractors()
        with open(exp_dir / "pairs.json", "w") as f:
            json.dump(cbn.to_json_pairs(), f, indent=4)

        # Step 3: Attractor Fields
        logger.info(f"[{experiment_name}] Step 3: Mounting stable attractor fields...")
        t3_start = time.perf_counter()
        cbn.mount_stable_attractor_fields()
        summary["performance"]["t_p3"] = time.perf_counter() - t3_start
        summary["results"]["n_fields"] = cbn.get_n_attractor_fields()
        with open(exp_dir / "fields.json", "w") as f:
            json.dump(cbn.to_json_fields(), f, indent=4)

        summary["status"] = "COMPLETED"

    except Exception as e:
        summary["status"] = "FAILED"
        summary["error"] = str(e)
        summary["traceback"] = traceback.format_exc()
        logger.error(f"[{experiment_name}] Pipeline failed: {e}")

        with open(exp_dir / "error_log.json", "w") as f:
            json.dump({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f, indent=4)

    finally:
        summary["total_time"] = time.perf_counter() - t_start
        with open(exp_dir / "execution_summary.json", "w") as f:
            json.dump(summary, f, indent=4)
        
        return summary # Retornamos el resumen para la consolidación global

def main():
    parser = argparse.ArgumentParser(description="CBN Production Processor")
    parser.add_argument("--config", type=str, required=True, help="Path to input JSON config")
    parser.add_argument("--output", type=str, default="results", help="Base directory for outputs")

    args = parser.parse_args()
    config_path = Path(args.config)
    output_base = Path(args.output)

    if not config_path.exists():
        print(f"Error: Configuration file {args.config} not found.")
        sys.exit(1)

    with open(config_path, "r") as f:
        data = json.load(f)

    configs = data if isinstance(data, list) else [data]

    logger.info(f"Starting processing for {len(configs)} configurations...")

    # Lista para acumular las métricas resumidas de todo el lote
    global_metrics = []

    for i, cfg in enumerate(configs):
        if not validate_config(cfg):
            logger.warning(f"Skipping invalid configuration at index {i}")
            continue

        exp_name = cfg.get("experiment_name", f"exp_{config_path.stem}_{i}")
        
        # Ejecutar y obtener resumen de la muestra
        res_summary = run_pipeline(cfg, exp_name, output_base)
        
        # Guardar solo datos numéricos y de estado esenciales para análisis estadístico rápida
        global_metrics.append({
            "experiment_name": res_summary["experiment_name"],
            "status": res_summary["status"],
            "total_time_seconds": res_summary["total_time"],
            "time_generation": res_summary["performance"].get("t_gen", 0.0),
            "time_p1_attractors": res_summary["performance"].get("t_p1", 0.0),
            "time_p2_pairs": res_summary["performance"].get("t_p2", 0.0),
            "time_p3_fields": res_summary["performance"].get("t_p3", 0.0),
            "n_local_attractors": res_summary["results"].get("n_local_attractors", 0),
            "n_pairs": res_summary["results"].get("n_pairs", 0),
            "n_fields": res_summary["results"].get("n_fields", 0)
        })

    # --- NUEVO: Exportación del reporte global consolidado ---
    global_report_path = output_base / "batch_execution_summary.json"
    with open(global_report_path, "w") as f:
        json.dump(global_metrics, f, indent=4)
    
    logger.info(f"Reporte global de rendimiento generado en: {global_report_path}")
    logger.info("All tasks processed.")

if __name__ == "__main__":
    main()