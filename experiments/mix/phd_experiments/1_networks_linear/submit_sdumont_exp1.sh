#!/bin/bash
#SBATCH --nodes=3            # Número de Nós
#SBATCH --ntasks-per-node=6  # Número de tarefas por Nó
#SBATCH --ntasks=18          # Número total de tarefas
#SBATCH -p cpu_shared        # Fila (partition) a ser utilizada
#SBATCH -J CRPT              # Nome do job
#SBATCH --mem=300G           # Memoria total solicitada
#SBATCH --time=48:00:00      # Tempo máximo de execução
#SBATCH -e log/slurm-%j.err  # Arquivo de erro
#SBATCH -o log/slurm-%j.out  # Arquivo de saída

# Cria os diretórios de log e tmp, se não existirem
mkdir -p log tmp
NETINFO=log/netinfo.$SLURM_JOBID.log

# Exibe os nós alocados para o Job
echo $SLURM_JOB_NODELIST

echo -n "Entering in: "
pwd
cd $SLURM_SUBMIT_DIR

# Coleta informações de rede
echo $SLURM_SUBMIT_HOST >> $NETINFO
ip addr >> $NETINFO

echo "Loading modules..."
# Carrega módulos necessários
module load python/3.8.2
module load minisat/2.2.0

echo "Creating the virtual environment..."
# Cria e ativa o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Atualiza pip e instala bibliotecas necessárias
pip install --upgrade pip
pip install --upgrade typeguard
pip install parsl satispy networkx pandas matplotlib

# Navega até o diretório de trabalho
cd /scratch/deephash/carlos.tovar/cbnetwork/experiments/1_networks_linear

echo "Starting Test Script"
export PYTHONPATH=/scratch/deephash/carlos.tovar/cbnetwork/:$PYTHONPATH
echo $PYTHONPATH
python3 exp1_linear_aleatory.py
