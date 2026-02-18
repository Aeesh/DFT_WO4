#!/usr/bin/env python3
"""
BAND STRUCTURE PLOTTING SCRIPT
Based on the tutorial you shared
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

# K-point labels for your monoclinic structure
KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

def read_fermi(scf_file):
    """Read Fermi energy from SCF output"""
    try:
        with open(scf_file, 'r') as f:
            for line in f:
                if 'the Fermi energy is' in line:
                    return float(line.split()[4])
    except:
        pass
    return None

def read_band_dat(band_file):
    """
    Read band data from bands.x output (.dat file)
    Returns: k_distance, bands_dict
    """
    coord_regex = r"^\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)$"

    k_coords = []
    bands = {}

    with open(band_file, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(coord_regex, line)

        if match:
            # Found k-point
            k_coords.append([float(match.group(1)),
                           float(match.group(2)),
                           float(match.group(3))])

            # Next lines have band energies
            i += 1
            band_energies = []

            while i < len(lines) and not re.match(coord_regex, lines[i]):
                band_energies.extend([float(x) for x in lines[i].split()])
                i += 1

            # Store in dictionary
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

    return np.array(k_dist), bands, k_coords

def find_high_symmetry_points(k_coords, k_dist):
    """Find positions of high-symmetry points"""
    hs_positions = [0.0]

    # Detect changes in k-path direction
    for i in range(1, len(k_coords) - 1):
        v1 = np.array(k_coords[i]) - np.array(k_coords[i-1])
        v2 = np.array(k_coords[i+1]) - np.array(k_coords[i])

        # Normalize
        v1 = v1 / (np.linalg.norm(v1) + 1e-10)
        v2 = v2 / (np.linalg.norm(v2) + 1e-10)

        # If direction changes
        if np.linalg.norm(v1 - v2) > 0.01:
            hs_positions.append(k_dist[i])

    hs_positions.append(k_dist[-1])
    return hs_positions

def plot_bands(band_file, fermi=None, output_file=None, title="Band Structure"):
    """Plot band structure"""

    # Read data
    k_dist, bands, k_coords = read_band_dat(band_file)

    # Find high-symmetry points
    hs_pos = find_high_symmetry_points(k_coords, k_dist)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Shift to Fermi level if available
    if fermi:
        ylabel = 'Energy - $E_F$ (eV)'
        shift = fermi
    else:
        ylabel = 'Energy (eV)'
        shift = 0.0

    # Plot all bands
    for band in bands.values():
        ax.plot(k_dist, np.array(band) - shift, 'b-', linewidth=0.8, alpha=0.7)

    # Fermi level
    if fermi:
        ax.axhline(0, color='red', linestyle='--', linewidth=1.5,
                  label='$E_F$', alpha=0.7)

    # High-symmetry lines
    for pos in hs_pos:
        ax.axvline(pos, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Labels
    ax.set_xticks(hs_pos)
    ax.set_xticklabels(KPOINT_LABELS[:len(hs_pos)])
    ax.set_ylabel(ylabel, fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlim(k_dist[0], k_dist[-1])
    ax.set_ylim(-8, 8)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
    else:
        plt.show()

    plt.close()

def main():
    """Plot all band structures"""
    print("="*80)
    print(" BAND STRUCTURE PLOTTER")
    print("="*80)

    compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
    mags = ['FM', 'AFM']

    output_dir = Path('band_plots')
    output_dir.mkdir(exist_ok=True)

    for compound in compounds:
        for mag in mags:
            print(f"\n📊 {compound} ({mag})...")

            # band_file = f"tmp/{compound}_{mag}/{compound}_{mag}_bands.dat"
            band_file = f"{compound}_{mag}_bands.dat"

            scf_file = f"scf_outputs/scf.{compound}_{mag}.out"

            if not Path(band_file).exists():
                print(f"  ⚠️  {band_file} not found")
                continue

            fermi = read_fermi(scf_file)
            if fermi:
                print(f"  ✅ Fermi: {fermi:.3f} eV")

            output = output_dir / f"{compound}_{mag}_bands.png"
            plot_bands(band_file, fermi, output, f"{compound} ({mag})")

    print("\n✅ Done! Plots in band_plots/")

if __name__ == "__main__":
    main()