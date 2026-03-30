import sys
import re
import math
import os
import subprocess
import shutil

# Unary materials
materials = [
"CoWO4", 
"CuWO4", 
"FeWO4", 
"MnWO4", 
"NiWO4", 
"ZnWO4"
]

for material in materials:
    run_file_template = f"""#!/bin/bash
#SBATCH -N 1
#SBATCH --partition=cpuonly     #cpuonly-debug
#SBATCH --ntasks-per-node=24
#SBATCH --job-name={material}_relax
#SBATCH -t 10:00:00
#SBATCH -o /trace/group/dabo/mansouro/jobs/_job-{material}-%j.out
#SBATCH -e /trace/group/dabo/mansouro/jobs/_job-{material}-%j.err

ulimit -s unlimited
export OMP_NUM_THREADS=1

echo "SLURM_NTASKS: " $SLURM_NTASKS
module purge
module load psc.allocations.user/1.0
module load intel-oneapi-compilers/2022.1.0 intel-oneapi-mkl/2022.1.0 intel-oneapi-mpi/2021.6.0

QE_DIR=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin

cd /trace/group/dabo/mansouro/unary/{material}

# Run SCF/Relax calculation
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in relax.{material}.in > relax.{material}.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -nk 4 -in scf.{material}.in > scf.{material}.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in bands.{material}.in > bands.{material}.out
# mpirun -np $SLURM_NTASKS $QE_DIR/bands.x -in {material}.bands.pp.in > {material}.bands.pp.out
# mpirun -np $SLURM_NTASKS $QE_DIR/pw.x -in nscf.{material}.in > nscf.{material}.out
mpirun -np $SLURM_NTASKS $QE_DIR/projwfc.x -pd .true. -in projwfc.{material}.in > projwfc.{material}.out
"""

    # Create the submission script
    script_dir = "/trace/group/dabo/mansouro/unary/scripts/"
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, f"run_{material}.sh")
    
    with open(script_path, "w") as sf:
        sf.write(run_file_template)
    os.chmod(script_path, 0o755)

    try:
        subprocess.run(["sbatch", script_path], check=True)
        print(f"Executed {script_path}")
    except subprocess.CalledProcessError as e:
        print(f"Execution failed with return code {e.returncode}")
    except Exception as e:
        print(f"Execution error: {e}")