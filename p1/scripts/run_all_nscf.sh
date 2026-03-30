#!/bin/bash
# run_all_nscf.sh
# Submit each .in file in nscf_inputs_FM and nscf_inputs_AFM as a separate SLURM job

INPUT_DIRS=("nscf_inputs_FM" "nscf_inputs_AFM")
OUTPUT_DIR="nscf_outputs"
LOG_DIR="nscf_logs"

mkdir -p $OUTPUT_DIR
mkdir -p $LOG_DIR
mkdir -p tmp

for DIR in "${INPUT_DIRS[@]}"; do
    for INFILE in $DIR/*.in; do
        BASENAME=$(basename $INFILE .in)

        echo "===== Starting submission for $BASENAME at $(date) ====="

        # Create temporary SLURM job script for this input
        JOBSCRIPT="$LOG_DIR/job_$BASENAME.sh"
        cat > $JOBSCRIPT << EOF
#!/bin/bash
#SBATCH --job-name=$BASENAME
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=24
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=$LOG_DIR/${BASENAME}.out
#SBATCH --error=$LOG_DIR/${BASENAME}.err

cd \$SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Create unique temp folder for this job
mkdir -p tmp/$BASENAME

mpirun -np \$SLURM_NTASKS \$QE_BIN -in $INFILE -outdir ./tmp/$BASENAME > $OUTPUT_DIR/nscf.$BASENAME.out

EOF

        # Submit the job
        sbatch $JOBSCRIPT

        echo "===== Finished submission for $BASENAME at $(date) ====="
    done
done
