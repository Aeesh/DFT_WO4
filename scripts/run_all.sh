#!/bin/bash
# submit_all_scf.sh
# This script submits each .in file in inputs_FM and inputs_AFM as a separate SLURM job

INPUT_DIRS=("inputs_FM" "inputs_AFM")
OUTPUT_DIR="outputs"
LOG_DIR="logs"

mkdir -p $OUTPUT_DIR
mkdir -p $LOG_DIR

for DIR in "${INPUT_DIRS[@]}"; do
    for INFILE in $DIR/*.in; do
        BASENAME=$(basename $INFILE .in)

        echo "===== Starting submission for $BASENAME at $(date) ====="

        # Create a temporary SLURM job script for this input
        JOBSCRIPT="$LOG_DIR/job_$BASENAME.sh"
        cat > $JOBSCRIPT << EOF
#!/bin/bash
#SBATCH --job-name=$BASENAME
#SBATCH --partition=cpuonly
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=16
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

mpirun -np \$SLURM_NTASKS \$QE_BIN -in $INFILE > $OUTPUT_DIR/scf.$BASENAME.out
EOF

        # Submit the job
        sbatch $JOBSCRIPT

        echo "===== Finished submission for $BASENAME at $(date) ====="
    done
done
