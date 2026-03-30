#!/bin/bash
# run_bands_postprocess.sh
# Post-process all band structure outputs with bands.x

INPUT_DIR="bands_inputs"
OUTPUT_DIR="bands_pp_outputs"

mkdir -p $OUTPUT_DIR

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0

BANDS_X=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/bands.x

for PPINFILE in $INPUT_DIR/*_bands_pp.in; do
    BASENAME=$(basename $PPINFILE _bands_pp.in)

    echo "Processing $BASENAME..."

    $BANDS_X < $PPINFILE > $OUTPUT_DIR/${BASENAME}_pp.out

    echo "✅ Done: $BASENAME"
done

echo ""
echo "All post-processing complete!"
echo "Band data files are in your tmp/ directories"
