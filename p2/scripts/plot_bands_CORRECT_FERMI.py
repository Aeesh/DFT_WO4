#!/usr/bin/env python3
"""
CORRECT BAND STRUCTURE PLOTTER
Calculates ACTUAL Fermi level from electron count
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

# Electron counts for each compound
ELECTRON_COUNTS = {
    'MnFeWO4': 107,
    'MnCoWO4': 108,
    'MnNiWO4': 109,
    'MnZnWO4': 111,
}

def read_band_dat(dat_file):
    """Read band data from .dat file"""
    k_coords = []
    bands = {}

    with open(dat_file, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if re.match(r'^[-\d.]+\s+[-\d.]+\s+[-\d.]+$', line):
            coords = [float(x) for x in line.split()]
            k_coords.append(coords)

            i += 1
            band_energies = []

            while i < len(lines):
                next_line = lines[i].strip()
                if re.match(r'^[-\d.]+\s+[-\d.]+\s+[-\d.]+$', next_line):
                    break
                if next_line:
                    band_energies.extend([float(x) for x in next_line.split()])
                i += 1

            for band_idx, energy in enumerate(band_energies):
                if band_idx not in bands:
                    bands[band_idx] = []
                bands[band_idx].append(energy)
        else:
            i += 1

    k_dist = [0.0]
    for i in range(1, len(k_coords)):
        dk = np.sqrt(sum((k_coords[i][j] - k_coords[i-1][j])**2 for j in range(3)))
        k_dist.append(k_dist[-1] + dk)

    return k_coords, bands, np.array(k_dist)

def find_high_symmetry_points(k_coords, k_dist):
    """Find high-symmetry point positions"""
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

def calculate_fermi_level(bands, n_electrons):
    """
    Calculate ACTUAL Fermi level from band energies and electron count
    For spin-polarized: n_electrons/2 per spin
    Fermi = average of HOMO and LUMO
    """
    n_occ = int(n_electrons / 2)  # Occupied bands per spin

    # Get all band energies
    all_energies = []
    for band_idx in sorted(bands.keys()):
        all_energies.extend(bands[band_idx])

    all_energies = sorted(all_energies)

    # Find HOMO (highest occupied) and LUMO (lowest unoccupied)
    # In sorted list, HOMO is at position that contains the last occupied electron
    # For all k-points and all bands, we have len(bands) * len(k-points) states per spin

    # But simpler: just look at band n_occ-1 (HOMO) and band n_occ (LUMO)
    if n_occ - 1 in bands and n_occ in bands:
        homo_energies = bands[n_occ - 1]
        lumo_energies = bands[n_occ]

        vbm = max(homo_energies)  # Highest occupied
        cbm = min(lumo_energies)  # Lowest unoccupied

        fermi = (vbm + cbm) / 2
        gap = cbm - vbm

        return fermi, vbm, cbm, gap

    return None, None, None, None

def plot_bands_with_fermi(dat_file, compound_name, output_file=None, title="Band Structure"):
    """
    Plot band structure with ACTUAL calculated Fermi level
    """
    print(f"\n📊 Plotting: {dat_file}")

    # Get electron count
    compound_base = compound_name.split('_')[0] if '_' in compound_name else compound_name
    n_elec = ELECTRON_COUNTS.get(compound_base)

    if not n_elec:
        print(f"  ⚠️  Don't know electron count for {compound_base}")
        n_elec = 108  # Default guess

    print(f"  📍 Electrons: {n_elec}")

    k_coords, bands, k_dist = read_band_dat(dat_file)

    if not bands:
        print(f"  ❌ No bands found!")
        return

    print(f"  ✅ Found {len(k_coords)} k-points, {len(bands)} bands")

    # Calculate ACTUAL Fermi level
    fermi, vbm, cbm, gap = calculate_fermi_level(bands, n_elec)

    if fermi:
        print(f"  📍 VBM: {vbm:.3f} eV")
        print(f"  📍 CBM: {cbm:.3f} eV")
        print(f"  📍 Fermi: {fermi:.3f} eV")
        print(f"  📍 Gap: {gap:.3f} eV")
    else:
        print(f"  ⚠️  Could not calculate Fermi level")
        fermi = 10  # Fallback

    hs_pos = find_high_symmetry_points(k_coords, k_dist)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot all bands shifted so Fermi = 0
    for band in bands.values():
        ax.plot(k_dist, [e - fermi for e in band], 'b-', linewidth=0.8, alpha=0.7)

    # High-symmetry lines
    for pos in hs_pos:
        ax.axvline(pos, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Fermi level now at 0
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5,
              label=f'Fermi = {fermi:.2f} eV', alpha=0.7, zorder=10)

    # VBM and CBM also shifted
    if vbm and cbm:
        ax.axhline(vbm - fermi, color='orange', linestyle=':', linewidth=1,
                  label=f'VBM = {vbm - fermi:.2f} eV', alpha=0.5, zorder=5)
        ax.axhline(cbm - fermi, color='purple', linestyle=':', linewidth=1,
                  label=f'CBM = {cbm - fermi:.2f} eV', alpha=0.5, zorder=5)


    # Labels
    ax.set_xticks(hs_pos)
    ax.set_xticklabels(KPOINT_LABELS[:len(hs_pos)])
    ax.set_ylabel('E - E$_F$ (eV)', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlim(k_dist[0], k_dist[-1])
    ax.set_ylim(-6, 6)

    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')

    # Add gap annotation
    if gap:
        ax.text(0.02, 0.02, f'Band Gap = {gap:.3f} eV',
               transform=ax.transAxes, fontsize=10,
               verticalalignment='bottom',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved: {output_file}")

    plt.close()

def main():
    """Plot all .dat files with CORRECT Fermi levels"""
    print("="*80)
    print(" CORRECTED BAND STRUCTURE PLOTTER")
    print(" (With ACTUAL calculated Fermi levels)")
    print("="*80)

    dat_files = [
        ('tmp/MnCoWO4_AFM/MnCoWO4_AFM_bands.dat', 'MnCoWO4_AFM'),
        ('tmp/MnCoWO4_FM/MnCoWO4_FM_bands.dat',   'MnCoWO4_FM'),
        ('tmp/MnFeWO4_FM/MnFeWO4_FM_bands.dat',   'MnFeWO4_FM'),
        ('tmp/MnNiWO4_AFM/MnNiWO4_AFM_bands.dat', 'MnNiWO4_AFM'),
        ('tmp/MnNiWO4_FM/MnNiWO4_FM_bands.dat',   'MnNiWO4_FM'),
        ('tmp/MnZnWO4_AFM/MnZnWO4_AFM_bands.dat', 'MnZnWO4_AFM'),
        ('tmp/MnZnWO4_FM/MnZnWO4_FM_bands.dat',   'MnZnWO4_FM'),
    ]

    import os
    os.makedirs('corrected_bands', exist_ok=True)

    for dat_file, name in dat_files:
        if Path(dat_file).exists():
            title = name.replace('_', ' ')
            output = f"corrected_bands/{name}_CORRECT.png"
            plot_bands_with_fermi(dat_file, name, output, title)
        else:
            print(f"\n⚠️  {dat_file} not found")

    print("\n" + "="*80)
    print(" ✅ DONE!")
    print("="*80)
    print("\nCorrected plots in: corrected_bands/")
    print("\nNOW with:")
    print("  - RED line = Actual Fermi level (calculated from electrons)")
    print("  - ORANGE line = VBM (valence band maximum)")
    print("  - PURPLE line = CBM (conduction band minimum)")
    print("  - Gap value shown in corner")

if __name__ == "__main__":
    main()