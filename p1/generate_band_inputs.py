#!/usr/bin/env python3
"""
AUTOMATED BAND STRUCTURE INPUT GENERATOR
Creates all input files for band structure calculations
"""

import os
import sys
from pathlib import Path

# Configuration
COMPOUNDS = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
MAG_CONFIGS = ['FM', 'AFM']

# Hubbard U values (eV)
U_VALUES = {
    'Mn': 4.65,
    'Fe': 7.08,
    'Co': 7.84,
    'Ni': 8.55,
    'Zn': 0.00  # Zn is d10, no U needed
}

# Default k-path for monoclinic P2/c (if SeeK-path not available)
# Based on standardized paths for monoclinic systems
DEFAULT_KPATH = [
    ('Gamma', [0.0000, 0.0000, 0.0000], 20),  # Γ
    ('Y',     [0.0000, 0.5000, 0.0000], 20),  # Y
    ('M',     [0.5000, 0.5000, 0.0000], 20),  # M
    ('Gamma', [0.0000, 0.0000, 0.0000], 20),  # Γ
    ('Z',     [0.0000, 0.0000, 0.5000], 20),  # Z
    ('A',     [0.5000, 0.5000, 0.5000], 1),   # A
]

def get_nscf_data(compound, mag):
    """
    Extract necessary data from NSCF input file
    Returns: atomic_positions, cell_parameters, atomic_species
    """
    nscf_file = f"nscf_inputs_{mag}/{compound}_{mag}.in"

    if not os.path.exists(nscf_file):
        print(f"⚠️  Warning: {nscf_file} not found")
        return None, None, None

    with open(nscf_file, 'r') as f:
        content = f.read()

    # Extract ATOMIC_POSITIONS
    atomic_positions = []
    in_positions = False
    for line in content.split('\n'):
        if 'ATOMIC_POSITIONS' in line:
            in_positions = True
            position_type = line.split()[1] if len(line.split()) > 1 else 'crystal'
            continue
        if in_positions:
            if line.strip() and not line.strip().startswith('K_POINTS') and not line.strip().startswith('CELL_'):
                atomic_positions.append(line.strip())
            else:
                break

    # Extract CELL_PARAMETERS
    cell_parameters = []
    in_cell = False
    for line in content.split('\n'):
        if 'CELL_PARAMETERS' in line:
            in_cell = True
            cell_type = line.split()[1] if len(line.split()) > 1 else 'angstrom'
            continue
        if in_cell:
            if line.strip() and not line.strip().startswith('HUBBARD'):
                cell_parameters.append(line.strip())
                if len(cell_parameters) == 3:
                    break

    # Extract ATOMIC_SPECIES
    atomic_species = []
    in_species = False
    for line in content.split('\n'):
        if 'ATOMIC_SPECIES' in line:
            in_species = True
            continue
        if in_species:
            if line.strip() and not line.strip().startswith('ATOMIC_POSITIONS'):
                atomic_species.append(line.strip())
            else:
                break

    return atomic_positions, cell_parameters, atomic_species

def generate_kpath_string(kpath=None):
    """
    Generate K_POINTS section for band structure calculation
    """
    if kpath is None:
        kpath = DEFAULT_KPATH

    total_points = sum(npts for _, _, npts in kpath)

    kpath_str = f"K_POINTS crystal_b\n"
    kpath_str += f"{len(kpath)}\n"

    for label, coords, npts in kpath:
        kpath_str += f"  {coords[0]:.4f}  {coords[1]:.4f}  {coords[2]:.4f}  {npts:3d}   ! {label}\n"

    return kpath_str

def create_band_input(compound, mag, atomic_positions, cell_parameters, atomic_species, output_dir):
    """
    Create band structure input file
    """
    # Determine which metals are present
    metal1 = 'Mn'
    metal2 = compound.replace('WO4', '').replace('Mn', '')

    # Magnetization values
    if mag == 'FM':
        mag1 = 0.20
        mag2 = 0.20
    else:  # AFM
        mag1 = 0.20
        mag2 = -0.20

    # Build input file
    input_text = f"""&CONTROL
  calculation = 'bands'
  prefix = '{compound}_{mag}'
  outdir = './tmp/{compound}_{mag}/'
  pseudo_dir = 'pseudo_dojo_pbesol/'
  verbosity = 'high'
/

&SYSTEM
  ibrav = 0
  nat = 12
  ntyp = 4
  ecutwfc = 120
  ecutrho = 480
  occupations = 'fixed'
  nspin = 2
  starting_magnetization(1) = {mag1}   ! {metal1}
  starting_magnetization(2) = {mag2}   ! {metal2}
  starting_magnetization(3) = 0.00   ! W
  starting_magnetization(4) = 0.00   ! O
  nbnd = 80
/

&ELECTRONS
  electron_maxstep = 150
  mixing_beta = 0.7
  conv_thr = 1.0e-9
  diagonalization = 'david'
/

ATOMIC_SPECIES
"""

    # Add atomic species
    for species in atomic_species:
        input_text += f"{species}\n"

    input_text += "\nATOMIC_POSITIONS crystal\n"

    # Add atomic positions
    for pos in atomic_positions:
        input_text += f"{pos}\n"

    # Add k-path
    input_text += "\n" + generate_kpath_string()

    # Add cell parameters
    input_text += "\nCELL_PARAMETERS angstrom\n"
    for cell in cell_parameters:
        input_text += f"{cell}\n"

    # Add Hubbard U (skip if both metals have no U)
    u1 = U_VALUES.get(metal1, 0.0)
    u2 = U_VALUES.get(metal2, 0.0)

    if u1 > 0 or u2 > 0:
        input_text += "\nHUBBARD {ortho-atomic}\n"
        if u1 > 0:
            input_text += f"U {metal1}-3d {u1}\n"
        if u2 > 0:
            input_text += f"U {metal2}-3d {u2}\n"

    # Write file
    output_file = output_dir / f"{compound}_{mag}_bands.in"
    with open(output_file, 'w') as f:
        f.write(input_text)

    print(f"✅ Created: {output_file}")
    return output_file

def create_bands_postprocess_input(compound, mag, output_dir):
    """
    Create input for bands.x post-processing
    """
    input_text = f"""&BANDS
  prefix = '{compound}_{mag}'
  outdir = './tmp/{compound}_{mag}/'
  filband = '{compound}_{mag}_bands.dat'
  lsym = .true.
/
"""

    output_file = output_dir / f"{compound}_{mag}_bands_pp.in"
    with open(output_file, 'w') as f:
        f.write(input_text)

    print(f"✅ Created: {output_file}")
    return output_file

def create_submission_script(output_dir):
    """
    Create SLURM submission script for all band calculations
    """
    script = """#!/bin/bash
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

cd \\$SLURM_SUBMIT_DIR
export OMP_NUM_THREADS=1

module purge
module load intel-oneapi-compilers/2022.1.0
module load intel-oneapi-mkl/2022.1.0
module load intel-oneapi-mpi/2021.6.0

QE_BIN=/trace/group/dabo/shared/software/qe/qe-7.4.1/build/bin/pw.x

# Run band structure calculation
mpirun -np \\$SLURM_NTASKS \\$QE_BIN -in $INFILE > $OUTPUT_DIR/$BASENAME.out

EOF

    # Submit the job
    sbatch $JOBSCRIPT

    echo "===== Submitted $BASENAME at $(date) ====="
done

echo ""
echo "All band calculations submitted!"
echo "Monitor with: squeue -u \\$USER"
"""

    output_file = output_dir / "run_all_bands.sh"
    with open(output_file, 'w') as f:
        f.write(script)

    os.chmod(output_file, 0o755)
    print(f"✅ Created: {output_file}")

def create_postprocess_script(output_dir):
    """
    Create script to run bands.x on all outputs
    """
    script = """#!/bin/bash
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
"""

    output_file = output_dir / "run_bands_postprocess.sh"
    with open(output_file, 'w') as f:
        f.write(script)

    os.chmod(output_file, 0o755)
    print(f"✅ Created: {output_file}")

def main():
    """
    Main function to generate all files
    """
    print("="*80)
    print(" AUTOMATED BAND STRUCTURE INPUT GENERATOR")
    print(" Binary (Mn,X)WO₄ Tungstates")
    print("="*80)

    # Create output directory
    output_dir = Path("bands_inputs")
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {output_dir}")
    print(f"\n🔧 Generating input files...\n")

    # Generate band structure inputs
    for compound in COMPOUNDS:
        for mag in MAG_CONFIGS:
            print(f"\n{'='*60}")
            print(f"  {compound} ({mag})")
            print('='*60)

            # Get data from NSCF input
            atomic_pos, cell_params, atomic_spec = get_nscf_data(compound, mag)

            if atomic_pos is None:
                print(f"⚠️  Skipping {compound}_{mag} - NSCF file not found")
                continue

            # Create band structure input
            create_band_input(compound, mag, atomic_pos, cell_params,
                            atomic_spec, output_dir)

            # Create bands.x post-processing input
            create_bands_postprocess_input(compound, mag, output_dir)

    print(f"\n{'='*80}")
    print(" Creating submission scripts...")
    print('='*80 + "\n")

    # Create submission script
    create_submission_script(output_dir)

    # Create post-processing script
    create_postprocess_script(output_dir)

    print("\n" + "="*80)
    print(" ✅ ALL FILES CREATED!")
    print("="*80)

    print("\n📋 NEXT STEPS:")
    print("  1. Review the generated input files in bands_inputs/")
    print("  2. Run: bash bands_inputs/run_all_bands.sh")
    print("  3. Wait for jobs to finish (~1-2 hours)")
    print("  4. Run: bash bands_inputs/run_bands_postprocess.sh")
    print("  5. Use plotting script to visualize results")

    print("\n📊 Generated files:")
    print(f"  • {len(COMPOUNDS) * len(MAG_CONFIGS)} band structure input files")
    print(f"  • {len(COMPOUNDS) * len(MAG_CONFIGS)} bands.x post-processing inputs")
    print("  • 1 submission script (run_all_bands.sh)")
    print("  • 1 post-processing script (run_bands_postprocess.sh)")

if __name__ == "__main__":
    main()