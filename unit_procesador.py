import argparse
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict

# Configuración de rutas para importaciones internas
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir / "cbn_python" / "src"))

from cbnetwork.cbnetwork import CBN
from cbnetwork.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def run_unit_pipeline(topology_path: Path, output_dir: Path):
    """
    Carga una topología CBN existente desde un JSON y ejecuta 
    los pasos de análisis (Atractores, Pares y Campos).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "experiment_name": output_dir.name,
        "source_topology": str(topology_path),
        "status": "STARTED",
        "performance": {},
        "results": {}
    }

    try:
        # Paso 0: Carga de Topología existente
        logger.info(f"Cargando topología desde {topology_path.name}...")
        t_start = time.perf_counter()
        
        # NOTA: Si el binding de C++ usa 'from_json', cambia 'load_from_json' por 'from_json'
        # Paso 0: Carga de Topología existente con detección dinámica
        logger.info(f"Cargando topología desde {topology_path.name}...")
        t_start = time.perf_counter()
        
        # Intentar las convenciones de nomenclatura más comunes de Jules
        if hasattr(CBN, 'from_json'):
            cbn = CBN.from_json(str(topology_path))
        elif hasattr(CBN, 'load_json'):
            cbn = CBN.load_json(str(topology_path))
        else:
            try:
                # Intentar cargar directo a través del constructor de la clase
                cbn = CBN(str(topology_path))
            except TypeError:
                # Si todo falla, listamos los métodos para saber el nombre exacto
                metodos_json = [m for m in dir(CBN) if 'json' in m.lower() or 'load' in m.lower()]
                raise AttributeError(
                    f"No se detectó el método de carga en la clase CBN.\n"
                    f"Métodos disponibles relacionados en tu compilación: {metodos_json}"
                )
        
        summary["performance"]["t_load"] = time.perf_counter() - t_start

        # Paso 1: Atractores Locales
        logger.info("Paso 1: Buscando atractores locales (Brute Force)...")
        t1_start = time.perf_counter()
        cbn.find_attractors_brute_force()
        summary["performance"]["t_p1"] = time.perf_counter() - t1_start
        summary["results"]["n_local_attractors"] = cbn.get_n_local_attractors()
        
        with open(output_dir / "attractors.json", "w") as f:
            json.dump(cbn.to_json_attractors(), f, indent=4)

        # Paso 2: Pares Compatibles
        logger.info("Paso 2: Buscando pares de atractores compatibles...")
        t2_start = time.perf_counter()
        cbn.find_compatible_pairs()
        summary["performance"]["t_p2"] = time.perf_counter() - t2_start
        summary["results"]["n_pairs"] = cbn.get_n_pair_attractors()
        
        with open(output_dir / "pairs.json", "w") as f:
            json.dump(cbn.to_json_pairs(), f, indent=4)

        # Paso 3: Campos Atractores
        logger.info("Paso 3: Ensamblando campos atractores estables...")
        t3_start = time.perf_counter()
        cbn.mount_stable_attractor_fields()
        summary["performance"]["t_p3"] = time.perf_counter() - t3_start
        summary["results"]["n_fields"] = cbn.get_n_attractor_fields()
        
        with open(output_dir / "fields.json", "w") as f:
            json.dump(cbn.to_json_fields(), f, indent=4)

        summary["status"] = "COMPLETED"
        logger.info(f"Análisis unitario completado exitosamente. Campos encontrados: {summary['results']['n_fields']}")

    except Exception as e:
        summary["status"] = "FAILED"
        summary["error"] = str(e)
        summary["traceback"] = traceback.format_exc()
        logger.error(f"El pipeline unitario falló: {e}")

        with open(output_dir / "error_log.json", "w") as f:
            json.dump({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f, indent=4)

    finally:
        summary["total_time"] = time.perf_counter() - t_start
        with open(output_dir / "execution_summary.json", "w") as f:
            json.dump(summary, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Procesador Unitario de CBN (Carga desde Topology)")
    parser.add_argument("--topology", type=str, required=True, help="Ruta al archivo topology.json de entrada")
    parser.add_argument("--output", type=str, default="unit_results", help="Directorio para guardar los JSON de salida")

    args = parser.parse_args()
    topology_path = Path(args.topology)
    output_dir = Path(args.output)

    if not topology_path.exists():
        logger.error(f"Error: Archivo de topología no encontrado en: {args.topology}")
        sys.exit(1)

    logger.info(f"Iniciando procesamiento unitario para: {topology_path.name}")
    run_unit_pipeline(topology_path, output_dir)
    logger.info("Proceso unitario finalizado.")

if __name__ == "__main__":
    main()