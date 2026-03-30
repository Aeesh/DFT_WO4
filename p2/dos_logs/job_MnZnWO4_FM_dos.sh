#!/bin/bash
#SBATCH --job-name=MnZnWO4_FM_dos
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=dos_logs/MnZnWO4_FM_dos.out
#SBATCH --error=dos_logs/MnZnWO4_FM_dos.err

cd $SLURM_SUBMIT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

DOS_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/dos.x

$DOS_BIN < dos_inputs_FM/MnZnWO4_FM_dos.in > dos_outputs/MnZnWO4_FM_dos.out

