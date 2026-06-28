import json
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

def validar_esquema(config: Dict[str, Any]) -> bool:
    """
    Asegura que todos los campos requeridos estén presentes en la configuración.
    """
    required_keys = [
        "n_networks",
        "v_topology",
        "n_var_network",
        "n_input_variables",
        "n_output_variables",
        "connectivity_density",
        "coupling_type"
    ]

    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        print(f"Error: Faltan las siguientes llaves en la configuración: {missing_keys}")
        return False
    return True

def generate_default_config(name: str = "default_experiment") -> Dict[str, Any]:
    """Genera una configuración por defecto válida."""
    return {
        "experiment_name": name,
        "n_networks": 4,
        "v_topology": 4, # Path
        "n_var_network": 3,
        "n_input_variables": 1,
        "n_output_variables": 1,
        "connectivity_density": 0.5,
        "coupling_type": "OR",
        "seed": 42
    }

def main():
    parser = argparse.ArgumentParser(description="Generador de configuraciones CBN (Source of Truth)")
    parser.add_argument("--output", type=str, default="config.json", help="Ruta del archivo de salida")
    parser.add_argument("--name", type=str, default="exp_01", help="Nombre del experimento")
    parser.add_argument("--batch", action="store_true", help="Generar un batch de configuraciones")

    args = parser.parse_args()

    configs = []
    if args.batch:
        # Ejemplo de batch: variando el número de redes
        for i in range(3, 7):
            cfg = generate_default_config(f"{args.name}_nets_{i}")
            cfg["n_networks"] = i
            configs.append(cfg)
    else:
        configs.append(generate_default_config(args.name))

    # Validar todas antes de escribir
    for cfg in configs:
        if not validar_esquema(cfg):
            sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(configs if args.batch else configs[0], f, indent=4)

    print(f"Configuración generada exitosamente en {output_path}")

if __name__ == "__main__":
    main()
