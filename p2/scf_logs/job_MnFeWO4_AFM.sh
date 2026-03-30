#!/bin/bash
#SBATCH --job-name=MnFeWO4_AFM
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=scf_logs/MnFeWO4_AFM.out
#SBATCH --error=scf_logs/MnFeWO4_AFM.err

cd $SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Create unique temp folder for this job
mkdir -p tmp/MnFeWO4_AFM

mpirun -np $SLURM_NTASKS $QE_BIN -in inputs_AFM/MnFeWO4_AFM.in -outdir ./tmp/MnFeWO4_AFM > scf_outputs/scf.MnFeWO4_AFM.out

