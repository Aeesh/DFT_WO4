#!/usr/bin/env python3
"""
Analyze DOS files and extract band gaps from Quantum ESPRESSO calculations
Generates a summary table of all systems
"""

import os
import numpy as np
import glob

def find_fermi_energy(dos_output_file):
    """Extract Fermi energy from DOS output file"""
    try:
        with open(dos_output_file, 'r') as f:
            for line in f:
                if 'Fermi energy' in line or 'E_Fermi' in line:
                    # Extract energy value
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'Fermi' in part or 'E_Fermi' in part:
                            try:
                                # Try to get the number after the keyword
                                ef = float(parts[i+2])
                                return ef
                            except:
                                pass
    except:
        pass
    return None

def analyze_dos_file(dos_file, fermi_energy):
    """
    Analyze DOS file to find band gap
    Returns: (band_gap, valence_band_max, conduction_band_min)
    """
    try:
        # Read DOS file
        data = np.loadtxt(dos_file)

        # Columns: Energy, DOS(up), DOS(down), Integrated_DOS
        # For spin-polarized: Energy, DOS(up), DOS(down), Integrated_DOS(up), Integrated_DOS(down)
        energy = data[:, 0]

        if data.shape[1] == 3:  # Non-spin-polarized
            dos = data[:, 1]
        else:  # Spin-polarized
            dos_up = data[:, 1]
            dos_down = data[:, 2]
            dos = dos_up + dos_down

        # Find indices below and above Fermi energy
        below_ef = energy < fermi_energy
        above_ef = energy > fermi_energy

        # Threshold for considering DOS as zero (states/eV)
        threshold = 0.01

        # Find valence band maximum (highest energy below Ef with non-zero DOS)
        valence_dos = dos[below_ef]
        valence_energy = energy[below_ef]

        # Find last non-zero DOS in valence band
        vbm_idx = None
        for i in range(len(valence_dos)-1, -1, -1):
            if valence_dos[i] > threshold:
                vbm_idx = i
                break

        if vbm_idx is None:
            return None, None, None

        vbm = valence_energy[vbm_idx]

        # Find conduction band minimum (lowest energy above Ef with non-zero DOS)
        conduction_dos = dos[above_ef]
        conduction_energy = energy[above_ef]

        cbm_idx = None
        for i in range(len(conduction_dos)):
            if conduction_dos[i] > threshold:
                cbm_idx = i
                break

        if cbm_idx is None:
            return None, None, None

        cbm = conduction_energy[cbm_idx]

        # Calculate band gap
        band_gap = cbm - vbm

        return band_gap, vbm, cbm

    except Exception as e:
        print(f"Error analyzing {dos_file}: {e}")
        return None, None, None

def main():
    """Analyze all DOS files and generate summary"""

    print("=" * 80)
    print("DOS Analysis - Band Gap Extraction")
    print("=" * 80)

    # Find all DOS output files
    dos_output_files = glob.glob('dos_outputs/*.out')

    if not dos_output_files:
        print("\nERROR: No DOS output files found in dos_outputs/")
        print("Make sure you've run the DOS calculations first!")
        return

    results = []

    for dos_output in sorted(dos_output_files):
        basename = os.path.basename(dos_output).replace('.out', '')
        system_name = basename.replace('_dos', '')

        # Find corresponding .dos file
        dos_file = f'dos_outputs/{system_name}.dos'

        if not os.path.exists(dos_file):
            dos_file = f'{system_name}.dos'

        if not os.path.exists(dos_file):
            print(f"\nWarning: Could not find .dos file for {system_name}")
            continue

        # Extract Fermi energy
        ef = find_fermi_energy(dos_output)

        if ef is None:
            print(f"\nWarning: Could not extract Fermi energy for {system_name}")
            continue

        # Analyze DOS
        band_gap, vbm, cbm = analyze_dos_file(dos_file, ef)

        if band_gap is None:
            print(f"\nWarning: Could not calculate band gap for {system_name}")
            continue

        results.append({
            'system': system_name,
            'fermi': ef,
            'vbm': vbm,
            'cbm': cbm,
            'gap': band_gap
        })

        print(f"\n{system_name}:")
        print(f"  Fermi Energy: {ef:.4f} eV")
        print(f"  VBM: {vbm:.4f} eV")
        print(f"  CBM: {cbm:.4f} eV")
        print(f"  Band Gap: {band_gap:.4f} eV")

    # Generate summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'System':<20} {'Fermi (eV)':<12} {'VBM (eV)':<12} {'CBM (eV)':<12} {'Gap (eV)':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['system']:<20} {r['fermi']:>11.4f} {r['vbm']:>11.4f} {r['cbm']:>11.4f} {r['gap']:>9.4f}")

    # Save to file
    with open('band_gaps_summary.txt', 'w') as f:
        f.write("Band Gap Analysis Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'System':<20} {'Fermi (eV)':<12} {'VBM (eV)':<12} {'CBM (eV)':<12} {'Gap (eV)':<10}\n")
        f.write("-" * 80 + "\n")
        for r in results:
            f.write(f"{r['system']:<20} {r['fermi']:>11.4f} {r['vbm']:>11.4f} {r['cbm']:>11.4f} {r['gap']:>9.4f}\n")

    print("\n" + "=" * 80)
    print("✓ Results saved to: band_gaps_summary.txt")
    print("=" * 80)

if __name__ == "__main__":
    main()