#!/bin/bash
#SBATCH --job-name=MnCoWO4_AFM_pdos
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=pdos_logs/MnCoWO4_AFM_pdos.out
#SBATCH --error=pdos_logs/MnCoWO4_AFM_pdos.err

cd $SLURM_SUBMIT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

PROJWFC_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/projwfc.x

$PROJWFC_BIN < pdos_inputs_AFM/MnCoWO4_AFM_pdos.in > pdos_outputs/MnCoWO4_AFM_pdos.out

