#!/bin/bash
#SBATCH --partition=cpuonly
#SBATCH -N 1
#SBATCH --ntasks-per-node=16
#SBATCH --mem=16G
#SBATCH -t 00:30:00

export OMP_NUM_THREADS=1

echo "SLURM_NTASKS: " $SLURM_NTASKS
module purge
module load psc.allocations.user/1.0
module load intel-oneapi-compilers/2022.1.0 intel-oneapi-mkl/2022.1.0 intel-oneapi-mpi/2021.6.0

QE_DIR=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin
mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in scf.in > scf.out
