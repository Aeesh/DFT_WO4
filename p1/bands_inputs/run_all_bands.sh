#!/bin/bash
# run_all_bands.sh
# Submit band structure calculations for all binary tungstates

INPUT_DIR="bands_inputs"
OUTPUT_DIR="bands_outputs"
LOG_DIR="bands_logs"

mkdir -p $OUTPUT_DIR
mkdir -p $LOG_DIR

for INFILE in $INPUT_DIR/*_bands.in; do
    BASENAME=$(basename $INFILE .in)

    echo "===== Submitting $BASENAME at $(date) ====="

    # Create SLURM job script
    JOBSCRIPT="$LOG_DIR/job_$BASENAME.sh"
    cat > $JOBSCRIPT << EOF
#!/bin/bash
#SBATCH --job-name=$BASENAME
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=$LOG_DIR/${BASENAME}.out
#SBATCH --error=$LOG_DIR/${BASENAME}.err

cd \$SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Run band structure calculation
mpirun -np \$SLURM_NTASKS \$QE_BIN -in $INFILE > $OUTPUT_DIR/$BASENAME.out

EOF

    # Submit the job
    sbatch $JOBSCRIPT

    echo "===== Submitted $BASENAME at $(date) ====="
done

echo ""
echo "All band calculations submitted!"
echo "Monitor with: squeue -u \$USER"
