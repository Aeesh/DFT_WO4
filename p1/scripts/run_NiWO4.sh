#!/bin/bash
#SBATCH --job-name=NiWO4_scf
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/NiWO4.log
#SBATCH --error=logs/NiWO4.err

# Ensure paths work
cd $SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

echo "Starting NiWO4 SCF at $(date)"

# Load Intel modules
module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

# QE binary
QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Run SCF calculation
mpirun -np $SLURM_NTASKS $QE_BIN -in inputs/scf.NiWO4.in > outputs/scf.NiWO4.out

echo "Finished NiWO4 SCF at $(date)"
