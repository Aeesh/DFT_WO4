#!/usr/bin/env python3
"""
SIMPLE BAND STRUCTURE PLOTTER
Plots the FULL energy range from .dat files
No Fermi shifting, shows everything
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

# K-point labels
KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

def read_band_dat(dat_file):
    """
    Read band data from .dat file
    Returns: k_coords, bands_dict, k_distance
    """
    k_coords = []
    bands = {}

    with open(dat_file, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match k-point line (3 numbers)
        if re.match(r'^[-\d.]+\s+[-\d.]+\s+[-\d.]+$', line):
            coords = [float(x) for x in line.split()]
            k_coords.append(coords)

            # Next lines have band energies
            i += 1
            band_energies = []

            while i < len(lines):
                next_line = lines[i].strip()
                # If it's another k-point, break
                if re.match(r'^[-\d.]+\s+[-\d.]+\s+[-\d.]+$', next_line):
                    break
                if next_line:
                    band_energies.extend([float(x) for x in next_line.split()])
                i += 1

            # Store bands
            for band_idx, energy in enumerate(band_energies):
                if band_idx not in bands:
                    bands[band_idx] = []
                bands[band_idx].append(energy)
        else:
            i += 1

    # Calculate k-distance
    k_dist = [0.0]
    for i in range(1, len(k_coords)):
        dk = np.sqrt(sum((k_coords[i][j] - k_coords[i-1][j])**2 for j in range(3)))
        k_dist.append(k_dist[-1] + dk)

    return k_coords, bands, np.array(k_dist)

def find_high_symmetry_points(k_coords, k_dist):
    """Find positions of high-symmetry points"""
    hs_positions = [0.0]

    for i in range(1, len(k_coords) - 1):
        v1 = np.array(k_coords[i]) - np.array(k_coords[i-1])
        v2 = np.array(k_coords[i+1]) - np.array(k_coords[i])

        v1 = v1 / (np.linalg.norm(v1) + 1e-10)
        v2 = v2 / (np.linalg.norm(v2) + 1e-10)

        if np.linalg.norm(v1 - v2) > 0.01:
            hs_positions.append(k_dist[i])

    hs_positions.append(k_dist[-1])
    return hs_positions

def plot_full_bands(dat_file, output_file=None, title="Band Structure"):
    """
    Plot FULL band structure - no Fermi shifting
    Shows all energies from lowest to highest
    """
    print(f"\n📊 Plotting: {dat_file}")

    # Read data
    k_coords, bands, k_dist = read_band_dat(dat_file)

    if not bands:
        print(f"  ❌ No bands found!")
        return

    print(f"  ✅ Found {len(k_coords)} k-points, {len(bands)} bands")

    # Find high-symmetry points
    hs_pos = find_high_symmetry_points(k_coords, k_dist)

    # Find energy range
    all_energies = []
    for band in bands.values():
        all_energies.extend(band)

    e_min = min(all_energies)
    e_max = max(all_energies)

    print(f"  📏 Energy range: {e_min:.1f} to {e_max:.1f} eV")

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot all bands (NO SHIFTING!)
    for band in bands.values():
        ax.plot(k_dist, band, 'b-', linewidth=0.8, alpha=0.7)

    # High-symmetry lines
    for pos in hs_pos:
        ax.axvline(pos, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Labels
    ax.set_xticks(hs_pos)
    ax.set_xticklabels(KPOINT_LABELS[:len(hs_pos)])
    ax.set_ylabel('Energy (eV)', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlim(k_dist[0], k_dist[-1])
    ax.set_ylim(e_min - 5, e_max + 5)  # Add 5 eV padding
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved: {output_file}")

    plt.close()

def main():
    """Plot all .dat files"""
    print("="*80)
    print(" FULL BAND STRUCTURE PLOTTER")
    print(" (Shows complete energy range)")
    print("="*80)

    # List of all your .dat files
    dat_files = [
        'MnCoWO4_AFM_bands.dat',
        'MnCoWO4_FM_bands.dat',
        'MnFeWO4_FM_bands.dat',
        'MnNiWO4_AFM_bands.dat',
        'MnNiWO4_FM_bands.dat',
        'MnZnWO4_AFM_bands.dat',
        'MnZnWO4_FM_bands.dat',
    ]

    # Create output directory
    import os
    os.makedirs('full_band_plots', exist_ok=True)

    for dat_file in dat_files:
        if Path(dat_file).exists():
            # Get system name
            name = dat_file.replace('_bands.dat', '').replace('_', ' ')

            # Output file
            output = f"full_band_plots/{dat_file.replace('.dat', '.png')}"

            # Plot
            plot_full_bands(dat_file, output, name)
        else:
            print(f"\n⚠️  {dat_file} not found")

    print("\n" + "="*80)
    print(" ✅ DONE!")
    print("="*80)
    print("\nPlots saved in: full_band_plots/")

if __name__ == "__main__":
    main()