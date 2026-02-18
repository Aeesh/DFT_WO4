#!/usr/bin/env python3
"""
Create Clean Band Structure Plots - Python 3.6 Compatible
Plots only relevant bands near Fermi level like the tutorial example
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

def read_bands_gnu(gnu_file):
    """
    Read the .gnu file created by bands.x
    This is the easiest format to parse
    """
    with open(gnu_file, 'r') as f:
        lines = f.readlines()

    k_points = []
    bands_data = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split()
        if len(parts) >= 2:
            k = float(parts[0])
            energy = float(parts[1])

            # Group by k-point
            if k not in k_points:
                k_points.append(k)

            k_idx = k_points.index(k)
            if k_idx not in bands_data:
                bands_data[k_idx] = []
            bands_data[k_idx].append(energy)

    # Convert to bands dictionary
    n_kpoints = len(k_points)
    n_bands = len(bands_data[0]) if 0 in bands_data else 0

    bands = {}
    for band_idx in range(n_bands):
        bands[band_idx] = []
        for k_idx in range(n_kpoints):
            if k_idx in bands_data and band_idx < len(bands_data[k_idx]):
                bands[band_idx].append(bands_data[k_idx][band_idx])

    return bands, k_points

def find_fermi_from_output(output_file):
    """
    Find Fermi energy from SCF or NSCF output
    """
    fermi = None

    # Try multiple possible output files
    possible_files = [
        output_file,
        output_file.replace('bands_outputs', 'nscf_outputs').replace('_bands', ''),
        output_file.replace('bands_outputs', 'outputs').replace('_bands', ''),
    ]

    for f in possible_files:
        if os.path.exists(f):
            try:
                with open(f, 'r') as file:
                    for line in file:
                        if 'Fermi energy' in line or 'the Fermi energy is' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                try:
                                    if 'Fermi' in part or 'energy' in part:
                                        fermi = float(parts[i+2])
                                        return fermi
                                except:
                                    pass
            except:
                pass

    return fermi

def plot_clean_bands(bands, k_distances, fermi_energy, system_name, output_file):
    """
    Plot bands near Fermi level (clean, like tutorial)
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Find relevant bands (within ±6 eV of Fermi)
    plot_range = 6.0  # eV
    relevant_bands = []

    for band_idx, energies in bands.items():
        energies_array = np.array(energies)
        if fermi_energy is not None:
            # Shift to E - E_F
            energies_shifted = energies_array - fermi_energy
            # Check if any part of this band is in our plotting range
            if np.any((energies_shifted > -plot_range) & (energies_shifted < plot_range)):
                relevant_bands.append(band_idx)
        else:
            relevant_bands.append(band_idx)

    print(f"  📊 Plotting {len(relevant_bands)} bands near Fermi level (out of {len(bands)} total)")

    # Plot selected bands
    for band_idx in relevant_bands:
        if band_idx in bands:
            energies = np.array(bands[band_idx])
            if fermi_energy is not None:
                energies = energies - fermi_energy
            ax.plot(k_distances, energies, 'k-', linewidth=0.8, alpha=0.6)

    # Plot Fermi level
    if fermi_energy is not None:
        ax.axhline(0, color='red', linestyle='--', linewidth=1.5,
                   label='$E_F$', alpha=0.7)
        ax.set_ylabel('Energy - $E_F$ (eV)', fontsize=13, fontweight='bold')
        ax.set_ylim(-plot_range, plot_range)
    else:
        ax.set_ylabel('Energy (eV)', fontsize=13, fontweight='bold')

    # Formatting
    ax.set_xlabel('k-path', fontsize=13, fontweight='bold')
    ax.set_title(f'Band Structure: {system_name}', fontsize=14, fontweight='bold')
    ax.set_xlim(min(k_distances), max(k_distances))

    if fermi_energy is not None:
        ax.legend(fontsize=10, loc='best')

    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Saved: {output_file}")

def process_all_systems():
    """
    Process all band structure calculations
    """
    systems = [
        'MnFeWO4_FM',
        'MnFeWO4_AFM',
        'MnCoWO4_FM',
        'MnCoWO4_AFM',
        'MnNiWO4_FM',
        'MnNiWO4_AFM',
        'MnZnWO4_FM',
        'MnZnWO4_AFM',
    ]

    os.makedirs('clean_band_plots', exist_ok=True)

    print("="*80)
    print(" CLEAN BAND STRUCTURE PLOTTING")
    print("="*80)

    for system_name in systems:
        print(f"\n📊 {system_name}...")

        # Look for .gnu file (easiest to parse)
        gnu_file = f"tmp/{system_name}/{system_name}_bands.dat.gnu"
        if not os.path.exists(gnu_file):
            gnu_file = f"{system_name}_bands.dat.gnu"

        if not os.path.exists(gnu_file):
            print(f"  ⚠️  {gnu_file} not found - skipping")
            continue

        # Read bands
        try:
            bands, k_distances = read_bands_gnu(gnu_file)
            print(f"  📈 Found {len(bands)} bands, {len(k_distances)} k-points")
        except Exception as e:
            print(f"  ❌ Failed to read {gnu_file}: {e}")
            continue

        # Find Fermi energy
        bands_output = f"bands_outputs/{system_name}_bands.out"
        fermi = find_fermi_from_output(bands_output)

        if fermi:
            print(f"  ⚡ Fermi energy: {fermi:.3f} eV")
        else:
            print(f"  ⚠️  Fermi energy not found, plotting raw energies")

        # Plot
        output_file = f"clean_band_plots/{system_name}_clean.png"
        plot_clean_bands(bands, k_distances, fermi, system_name, output_file)

    print("\n" + "="*80)
    print(" ✅ DONE!")
    print("="*80)
    print("\nClean band plots saved in: clean_band_plots/")
    print("These show only bands near Fermi level (like your PI's example)")

if __name__ == "__main__":
    print("\n🎯 Creating Clean Band Structure Plots (Python 3.6 Compatible)\n")
    process_all_systems()