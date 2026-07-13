import argparse
import json
import logging
import os
import sys
import time
import traceback
import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Búsqueda dinámica de la raíz del proyecto (cbn_core)
current_dir = Path(__file__).resolve().parent
root_dir = current_dir
while not (root_dir / "cbn_python").exists() and root_dir.parent != root_dir:
    root_dir = root_dir.parent

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

def load_identical_cbn(topology_path: Path) -> CBN:
    """Helper para cargar una CBN limpia desde el JSON y evitar contaminación de caché."""
    if hasattr(CBN, 'from_json'):
        return CBN.from_json(str(topology_path))
    elif hasattr(CBN, 'load_json'):
        return CBN.load_json(str(topology_path))
    else:
        return CBN(str(topology_path))

def execute_profile(cbn: CBN, profile: str) -> Tuple[float, float, float, float, int, int, int]:
    """Ejecuta los métodos exactos de C++ correspondientes al perfil y retorna sus métricas."""
    t_p1 = t_p2 = t_p3 = 0.0

    if profile == "seq":
        t0 = time.perf_counter()
        cbn.find_attractors_duvrova()
        t_p1 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.find_compatible_pairs()
        t_p2 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.mount_stable_attractor_fields()
        t_p3 = time.perf_counter() - t0

    elif profile == "par":
        t0 = time.perf_counter()
        cbn.find_local_attractors_parallel()
        t_p1 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.find_compatible_pairs_parallel()
        t_p2 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.mount_stable_attractor_fields_parallel()
        t_p3 = time.perf_counter() - t0

    elif profile == "weights":
        t0 = time.perf_counter()
        cbn.find_local_attractors_parallel_with_weights()
        t_p1 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.find_compatible_pairs_parallel_with_weights()
        t_p2 = time.perf_counter() - t0

        t0 = time.perf_counter()
        cbn.mount_stable_attractor_fields_parallel_chunks()
        t_p3 = time.perf_counter() - t0

    total_t = t_p1 + t_p2 + t_p3
    
    # Extraer métricas topológicas de la red resuelta
    n_attr = cbn.get_n_local_attractors()
    n_pairs = cbn.get_n_pair_attractors()
    n_fields = cbn.get_n_attractor_fields()

    return t_p1, t_p2, t_p3, total_t, n_attr, n_pairs, n_fields

def run_pipeline(config: Dict[str, Any], sample_id: int, experiment_name: str, output_base: Path) -> List[Dict[str, Any]]:
    """Genera la topología base, la guarda, y la procesa con los 3 métodos."""
    exp_dir = output_base / experiment_name
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    n_nets = config.get("n_networks", 0)
    metrics_list = []

    try:
        # 1. Generar la "Red Maestra" y guardarla
        logger.info(f"[{experiment_name}] Generando topología base...")
        cbn_base = CBN.generate_from_config(config)
        topo_path = exp_dir / "topology.json"
        cbn_base.to_json(str(topo_path))

        # 2. Ejecutar los 3 perfiles sobre copias idénticas
        profiles = ["seq", "par", "weights"]
        
        for profile in profiles:
            logger.info(f"[{experiment_name}] Ejecutando perfil: {profile.upper()}...")
            
            # Cargar red limpia sin resolver
            cbn_instance = load_identical_cbn(topo_path)
            
            # Procesar y medir tiempos
            tp1, tp2, tp3, total, n_attr, n_pairs, n_fields = execute_profile(cbn_instance, profile)
            
            # Guardar resultados
            metrics_list.append({
                "sample": sample_id,
                "n_nets": n_nets,
                "perfil": profile,
                "t_p1": tp1,
                "t_p2": tp2,
                "t_p3": tp3,
                "total_t": total,
                "n_attractors": n_attr,
                "n_pairs": n_pairs,
                "n_fields": n_fields
            })

            # (Opcional) Guardar JSONs específicos por método para depuración
            with open(exp_dir / f"fields_{profile}.json", "w") as f:
                json.dump(cbn_instance.to_json_fields(), f, indent=4)

    except Exception as e:
        logger.error(f"[{experiment_name}] Falló el pipeline: {e}")
        with open(exp_dir / "error_log.json", "w") as f:
            json.dump({"error": str(e), "traceback": traceback.format_exc()}, f, indent=4)

    return metrics_list

def main():
    parser = argparse.ArgumentParser(description="CBN All-in-One Benchmark Processor")
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

    logger.info(f"Iniciando evaluación 3-en-1 para {len(configs)} configuraciones...")

    all_metrics = []

    for i, cfg in enumerate(configs):
        if not validate_config(cfg):
            logger.warning(f"Saltando configuración inválida en índice {i}")
            continue

        sample_id = i + 1
        exp_name = cfg.get("experiment_name", f"exp_{config_path.stem}_{sample_id}")
        
        # Ejecuta la red 3 veces (1 por método) y retorna 3 filas de datos
        sample_metrics = run_pipeline(cfg, sample_id, exp_name, output_base)
        all_metrics.extend(sample_metrics)

    # --- CONFIGURAR CSV EN TIEMPO REAL ---
    csv_path = output_base / "benchmark_granular_workflow.csv"
    fieldnames = ["sample", "n_nets", "perfil", "t_p1", "t_p2", "t_p3", "total_t", "n_attractors", "n_pairs", "n_fields"]
    
    # Crear el archivo y escribir la cabecera antes del bucle
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    logger.info(f"Iniciando evaluación 3-en-1 para {len(configs)} configuraciones...")

    for i, cfg in enumerate(configs):
        if not validate_config(cfg):
            logger.warning(f"Saltando configuración inválida en índice {i}")
            continue

        sample_id = i + 1
        exp_name = cfg.get("experiment_name", f"exp_{config_path.stem}_{sample_id}")
        
        # Ejecutar la red (retorna las 3 filas de la muestra actual)
        sample_metrics = run_pipeline(cfg, sample_id, exp_name, output_base)
        
        # 👈 ESCRIBIR INMEDIATAMENTE AL CSV (Modo Append 'a')
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for row in sample_metrics:
                row_formatted = {k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()}
                writer.writerow(row_formatted)
                
        logger.info(f"==> Muestra {sample_id}/{len(configs)} guardada en CSV.")

    logger.info(f"¡Benchmark completado con éxito! Datos finales en: {csv_path}")

if __name__ == "__main__":
    main()