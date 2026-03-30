#!/bin/bash
#SBATCH --job-name=NiWO4_scf
#SBATCH --output=logs/NiWO4.log
#SBATCH --ntasks=16
#SBATCH --time=02:00:00
#SBATCH --partition=batch       

module load quantumespresso/7.2-nvhpc22.7-mkl

pw.x < inputs/scf.NiWO4.in > outputs/scf.NiWO4.out
