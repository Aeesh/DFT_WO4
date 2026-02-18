#!/usr/bin/env python3
"""
Generate DOS and PDOS input files for Quantum ESPRESSO calculations
Automatically creates input files for all binary tungstate systems
"""

import os

# Define all your systems
systems_FM = [
    'MnCoWO4_FM',
    'MnFeWO4_FM',
    'MnNiWO4_FM',
    'MnZnWO4_FM'
]

systems_AFM = [
    'MnCoWO4_AFM',
    'MnFeWO4_AFM',
    'MnNiWO4_AFM',
    'MnZnWO4_AFM'
]

# Energy range for DOS (adjust if needed)
EMIN = -20.0
EMAX = 30.0
DELTAE = 0.01

def create_dos_input(system_name, magnetic_type):
    """Create DOS input file for a given system"""

    content = f"""&DOS
prefix = '{system_name}'
outdir = './tmp/{system_name}/'
fildos = '{system_name}.dos'
emin = {EMIN}
emax = {EMAX}
deltae = {DELTAE}
/
"""

    return content

def create_pdos_input(system_name, magnetic_type):
    """Create PDOS input file for a given system"""

    content = f"""&PROJWFC
prefix = '{system_name}'
outdir = './tmp/{system_name}/'
filpdos = '{system_name}'
emin = {EMIN}
emax = {EMAX}
deltae = {DELTAE}
/
"""

    return content

def main():
    """Generate all DOS and PDOS input files"""

    # Create directories
    os.makedirs('dos_inputs_FM', exist_ok=True)
    os.makedirs('dos_inputs_AFM', exist_ok=True)
    os.makedirs('pdos_inputs_FM', exist_ok=True)
    os.makedirs('pdos_inputs_AFM', exist_ok=True)

    print("=" * 60)
    print("Generating DOS and PDOS input files")
    print("=" * 60)

    # Generate DOS inputs for FM systems
    print("\n--- FM Systems (DOS) ---")
    for system in systems_FM:
        filename = f'dos_inputs_FM/{system}_dos.in'
        content = create_dos_input(system, 'FM')
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✓ Created: {filename}")

    # Generate DOS inputs for AFM systems
    print("\n--- AFM Systems (DOS) ---")
    for system in systems_AFM:
        filename = f'dos_inputs_AFM/{system}_dos.in'
        content = create_dos_input(system, 'AFM')
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✓ Created: {filename}")

    # Generate PDOS inputs for FM systems
    print("\n--- FM Systems (PDOS) ---")
    for system in systems_FM:
        filename = f'pdos_inputs_FM/{system}_pdos.in'
        content = create_pdos_input(system, 'FM')
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✓ Created: {filename}")

    # Generate PDOS inputs for AFM systems
    print("\n--- AFM Systems (PDOS) ---")
    for system in systems_AFM:
        filename = f'pdos_inputs_AFM/{system}_pdos.in'
        content = create_pdos_input(system, 'AFM')
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✓ Created: {filename}")

    print("\n" + "=" * 60)
    print(f"✓ Successfully generated all input files!")
    print(f"  - DOS inputs: 8 files (4 FM + 4 AFM)")
    print(f"  - PDOS inputs: 8 files (4 FM + 4 AFM)")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: bash run_all_dos.sh")
    print("2. Run: bash run_all_pdos.sh")
    print("3. Analyze the output .dos and .pdos files")
    print("=" * 60)

if __name__ == "__main__":
    main()