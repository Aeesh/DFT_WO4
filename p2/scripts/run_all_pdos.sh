#!/bin/bash
# run_all_pdos.sh
# Submit PDOS calculations for all binary tungstate systems

INPUT_DIRS=("pdos_inputs_FM" "pdos_inputs_AFM")
OUTPUT_DIR="pdos_outputs"
LOG_DIR="pdos_logs"

mkdir -p $OUTPUT_DIR
mkdir -p $LOG_DIR

echo "=================================================="
echo "Submitting PDOS calculations"
echo "=================================================="

for DIR in "${INPUT_DIRS[@]}"; do
    echo ""
    echo "Processing directory: $DIR"
    echo "--------------------------------------------------"

    for INFILE in $DIR/*.in; do
        BASENAME=$(basename $INFILE .in)

        echo "Submitting: $BASENAME"

        JOBSCRIPT="$LOG_DIR/job_$BASENAME.sh"
        cat > $JOBSCRIPT << EOF
#!/bin/bash
#SBATCH --job-name=$BASENAME
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=$LOG_DIR/${BASENAME}.out
#SBATCH --error=$LOG_DIR/${BASENAME}.err

cd \$SLURM_SUBMIT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

PROJWFC_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/projwfc.x

\$PROJWFC_BIN < $INFILE > $OUTPUT_DIR/${BASENAME}.out

EOF

        sbatch $JOBSCRIPT
    done
done

echo ""
echo "=================================================="
echo "All PDOS jobs submitted!"
echo "Check status with: squeue -u \$USER"
echo "=================================================="