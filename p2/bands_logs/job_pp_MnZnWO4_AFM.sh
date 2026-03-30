#!/bin/bash
#SBATCH --job-name=pp_MnZnWO4_AFM
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=bands_logs/pp_MnZnWO4_AFM.out
#SBATCH --error=bands_logs/pp_MnZnWO4_AFM.err

cd $SLURM_SUBMIT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

BANDS_X=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/bands.x

mpirun -np 1 $BANDS_X < bands_inputs/MnZnWO4_AFM_bands_pp.in > bands_pp_outputs/MnZnWO4_AFM_pp.out
