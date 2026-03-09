#!/bin/bash
#SBATCH --job-name=MnNiWO4_scf
#SBATCH --output=logs/MnNiWO4.log
#SBATCH --ntasks=16
#SBATCH --time=05:00:00
#SBATCH --partition=batch       

module load quantumespresso/7.2-nvhpc22.7-mkl

pw.x < inputs/scf.MnNiWO4.in > outputs/scf.MnNiWO4.out
