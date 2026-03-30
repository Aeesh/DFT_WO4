#!/bin/bash
#SBATCH --job-name=MnNiWO4_AFM
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=nscf_logs/MnNiWO4_AFM.out
#SBATCH --error=nscf_logs/MnNiWO4_AFM.err

cd $SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Create unique temp folder for this job
mkdir -p tmp/MnNiWO4_AFM

mpirun -np $SLURM_NTASKS $QE_BIN -in nscf_inputs_AFM/MnNiWO4_AFM.in -outdir ./tmp/MnNiWO4_AFM > nscf_outputs/nscf.MnNiWO4_AFM.out

