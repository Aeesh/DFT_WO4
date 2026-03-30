#!/bin/bash
# run_bands_x_postprocessing.sh
# Run bands.x post-processing on all systems using full path

# Path to Quantum ESPRESSO binaries
QE_DIR="/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin"
BANDS_X="${QE_DIR}/bands.x"

# Check if bands.x exists
if [ ! -f "$BANDS_X" ]; then
    echo "❌ bands.x not found at: $BANDS_X"
    echo "Please update the QE_DIR path in this script"
    exit 1
fi

echo "✅ Found bands.x at: $BANDS_X"
echo ""

# Load modules
module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

# Create output directory
mkdir -p bands_pp_outputs

echo "================================================================================  "
echo " RUNNING BANDS.X POST-PROCESSING"
echo "================================================================================"

# Process each _pp.in file
for PP_INPUT in bands_inputs/*_pp.in; do
    BASENAME=$(basename "$PP_INPUT" _pp.in)

    echo ""
    echo "Processing: $BASENAME"
    echo "----------------------------------------"

    # Run bands.x
    $BANDS_X < "$PP_INPUT" > "bands_pp_outputs/${BASENAME}_pp.out" 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✅ bands.x completed successfully"

        # Check if .dat file was created
        SYSTEM_NAME=$(echo $BASENAME | sed 's/_bands_pp//')
        DAT_FILE="tmp/${SYSTEM_NAME}/${SYSTEM_NAME}_bands.dat"

        if [ -f "$DAT_FILE" ]; then
            echo "  ✅ Created: $DAT_FILE"
        else
            echo "  ⚠️  .dat file not found at expected location"
        fi
    else
        echo "  ❌ bands.x failed - check bands_pp_outputs/${BASENAME}_pp.out for errors"
    fi
done

echo ""
echo "================================================================================"
echo " ✅ DONE!"
echo "================================================================================"
echo ""
echo "Output files in: bands_pp_outputs/"
echo "Band data files in: tmp/[system_name]/[system_name]_bands.dat"
echo ""
echo "Next: Run python3 create_clean_band_plots.py to generate plots"