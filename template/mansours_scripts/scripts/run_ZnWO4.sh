#!/bin/bash
#SBATCH -N 1
#SBATCH --partition=cpuonly     #cpuonly-debug
#SBATCH --ntasks-per-node=24
#SBATCH --job-name=ZnWO4_relax
#SBATCH -t 10:00:00
#SBATCH -o /trace/group/dabo/mansouro/jobs/_job-ZnWO4-%j.out
#SBATCH -e /trace/group/dabo/mansouro/jobs/_job-ZnWO4-%j.err

ulimit -s unlimited
export OMP_NUM_THREADS=1

echo "SLURM_NTASKS: " $SLURM_NTASKS
module purge
module load psc.allocations.user/1.0
module load intel-oneapi-compilers/2022.1.0 intel-oneapi-mkl/2022.1.0 intel-oneapi-mpi/2021.6.0

QE_DIR=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin

cd /trace/group/dabo/mansouro/unary/ZnWO4

# Run SCF/Relax calculation
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in relax.ZnWO4.in > relax.ZnWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in scf.ZnWO4.in > scf.ZnWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in bands.ZnWO4.in > bands.ZnWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/bands.x -in ZnWO4.bands.pp.in > ZnWO4.bands.pp.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in nscf.ZnWO4.in > nscf.ZnWO4.out
mpirun -np $SLURM_NTASKS $QE_DIR/projwfc.x -pd .true. -in projwfc.ZnWO4.in > projwfc.ZnWO4.out
