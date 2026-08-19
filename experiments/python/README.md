source .venv/bin/activate

# CBN Core: High-Performance Stationary-Coupled Modular Boolean Networks

This repository contains the source code and experimental framework for the paper **"Stationary-Coupled Modular Boolean Networks: Formalization, Complexity Bounds, and High-Performance C++ Engine"**, to be presented at *Complex Networks 2026*.

## Repository Structure
- `main_gerador.py`: Generates synthetic coupled network topologies and exports configurations in JSON format.
- `main_processor_weights.py`: The optimized Python baseline implementation (Strong Baseline).
- `main_processor_parallel.py`: Multi-threaded processor utilizing Python's multiprocessing.
- `main_processor_sequential.py`: Basic sequential reference implementation.
- `unit_processor_sequential.py`: Debugging and unit testing script for single modules.

## Getting Started
To reproduce the experiments, ensure you have Python 3.x installed with the necessary dependencies:

```bash
pip install -r requirements.txt


## Configuration Factory (`experiment_template_generator.py`)

The configuration factory is responsible for generating validated JSON inputs for the C++ and Python processing engines. It supports both custom isolated experiments and automated batch exploration grids.

### Usage & Arguments

| Argument | Type | Default | Description |
| :--- | :---: | :---: | :stringify |
| `--output` | `str` | `config.json` | Path to the target output JSON file. |
| `--name` | `str` | `exp_custom` | Base prefix name for the experiments. |
| `--samples` | `int` | `1` | Number of independent stochastic samples. |
| `--networks` | `int` | `4` | Number of local modules ($m$). |
| `--topology` | `int` | `4` | Topological arrangement type identifier. |
| `--vars` | `int` | `6` | Internal Boolean variables per local module ($n_j$). |
| `--inputs` | `int` | `2` | Number of incoming coupling variables ($|\mathcal{E}^j|$). |
| `--outputs` | `int` | `2` | Number of emitted coupling signals ($|\mathcal{S}^j|$). |
| `--density` | `float` | `0.3` | Inter-modular connectivity density. |
| `--coupling` | `str` | `NONE` | Coupling logic (`NONE`, `OR`, `XOR`, `AND`, `IDENTITY`). |
| `--seed` | `int` | `42` | Base pseudo-random number generator seed. |
| `--variable-names`| `str` | `None` | Comma-separated custom names for local variables. |
| `--batch` | `flag` | `False` | Triggers the automated multi-variable batch grid. |

### Examples

1. **Generate a Single Custom Configuration with Custom Gene Labels:**
   ```bash
   python experiment_template_generator.py --networks 4 --vars 3 --variable-names "CyclinE,CDK2,RB1" --coupling XOR --output config_cell_cycle.json