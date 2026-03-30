#!/bin/bash
# run_bands_postprocess.sh
# Submits bands.x post-processing as SLURM jobs

INPUT_DIR="bands_inputs"
OUTPUT_DIR="bands_pp_outputs"
LOG_DIR="bands_logs"

mkdir -p $OUTPUT_DIR

for PPINFILE in $INPUT_DIR/*_bands_pp.in; do
    BASENAME=$(basename $PPINFILE _bands_pp.in)

    echo "Submitting post-processing for $BASENAME..."

    JOBSCRIPT="$LOG_DIR/job_pp_$BASENAME.sh"
    cat > $JOBSCRIPT << EOF
#!/bin/bash
#SBATCH --job-name=pp_$BASENAME
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=$LOG_DIR/pp_${BASENAME}.out
#SBATCH --error=$LOG_DIR/pp_${BASENAME}.err

cd \$SLURM_SUBMIT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

BANDS_X=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/bands.x

mpirun -np 1 \$BANDS_X < $PPINFILE > $OUTPUT_DIR/${BASENAME}_pp.out
EOF

    sbatch $JOBSCRIPT
    echo "✅ Submitted: $BASENAME"
done

echo ""
echo "All post-processing jobs submitted!"
echo "Monitor with: squeue -u \$USER"