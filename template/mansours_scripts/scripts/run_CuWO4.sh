#!/bin/bash
#SBATCH -N 1
#SBATCH --partition=cpuonly     #cpuonly-debug
#SBATCH --ntasks-per-node=24
#SBATCH --job-name=CuWO4_relax
#SBATCH -t 10:00:00
#SBATCH -o /trace/group/dabo/mansouro/jobs/_job-CuWO4-%j.out
#SBATCH -e /trace/group/dabo/mansouro/jobs/_job-CuWO4-%j.err

ulimit -s unlimited
export OMP_NUM_THREADS=1

echo "SLURM_NTASKS: " $SLURM_NTASKS
module purge
module load psc.allocations.user/1.0
module load intel-oneapi-compilers/2022.1.0 intel-oneapi-mkl/2022.1.0 intel-oneapi-mpi/2021.6.0

QE_DIR=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin

cd /trace/group/dabo/mansouro/unary/CuWO4

# Run SCF/Relax calculation
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in relax.CuWO4.in > relax.CuWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in scf.CuWO4.in > scf.CuWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in bands.CuWO4.in > bands.CuWO4.out
# mpirun -np $SLURM_NTASKS $QE_DIR/bands.x -in CuWO4.bands.pp.in > CuWO4.bands.pp.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in nscf.CuWO4.in > nscf.CuWO4.out
mpirun -np $SLURM_NTASKS $QE_DIR/projwfc.x -pd .true. -in projwfc.CuWO4.in > projwfc.CuWO4.out
