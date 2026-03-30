#!/bin/bash
#SBATCH --job-name=MnWO4_scf
#SBATCH --output=logs/MnWO4.log
#SBATCH --ntasks=16
#SBATCH --time=02:00:00
#SBATCH --partition=batch       

module load quantumespresso/7.2-nvhpc22.7-mkl

pw.x < inputs/scf.MnWO4.in > outputs/scf.MnWO4.out
