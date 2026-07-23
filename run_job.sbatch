#!/bin/bash
#SBATCH --job-name=cbn_processor
#SBATCH --output=/scratch/deephash/carlos.tovar/cbn_core/experiments/mix/results/proc_%j.out
#SBATCH --error=/scratch/deephash/carlos.tovar/cbn_core/experiments/mix/results/proc_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --partition=sequana_cpu
#SBATCH --time=12:00:00

echo "=== INICIO DEL PROCESAMIENTO EN SDUMONT ==="
date

# 1. Posicionarse en la ruta correcta del experimento
cd /scratch/deephash/carlos.tovar/cbn_core/experiments/mix

# 2. Activar entorno virtual
source ../../venv/bin/activate
module load minisat/2.2.0_sequana

# 3. Ejecutar el procesador con el JSON problemático (o el que necesites)
python3 main_processor_py_cpp.py --config aleatory_fixed.json

echo "=== FIN DEL PROCESAMIENTO ==="
date