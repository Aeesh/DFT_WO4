#!/bin/bash
#SBATCH --job-name=MnCoWO4_FM_bands
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=bands_logs/MnCoWO4_FM_bands.out
#SBATCH --error=bands_logs/MnCoWO4_FM_bands.err

cd $SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Run band structure calculation
mpirun -np $SLURM_NTASKS $QE_BIN -in bands_inputs/MnCoWO4_FM_bands.in > bands_outputs/MnCoWO4_FM_bands.out

