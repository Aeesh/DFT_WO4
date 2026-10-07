#!/usr/bin/env python3
"""
FIXED BAND STRUCTURE PLOTTER
- Uses SCF Fermi energy (correct for spin-polarised systems)
# - Shifts all bands so E_F = 0
- Computes VBM and CBM correctly using the Fermi level as separator
- Shows a sensible energy window around E_F
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

# -----------------------------------------------------------------------
# Fermi energies read directly from SCF output files.
# How to find yours: grep "the Fermi energy" your_scf_output.out
# -----------------------------------------------------------------------
FERMI_FROM_SCF = {
    'MnCoWO4_AFM': 12.4323,
    'MnCoWO4_FM':  12.4714,
    'MnFeWO4_FM':  12.6410,
    'MnNiWO4_AFM': 11.9136,
    'MnNiWO4_FM':  11.9606,
    'MnZnWO4_AFM': 11.2876,
    'MnZnWO4_FM':  11.2876,
}


def read_band_dat(dat_file):
    """
    Read band energies from a bands.x .dat file.
    Returns: k_coords (list), bands (dict: band_idx -> list of energies), k_dist (array)
    """
    k_coords = []
    bands = {}

    with open(dat_file, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # A k-point line has exactly 3 floats
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

    # Build cumulative k-distance for x-axis
    k_dist = [0.0]
    for i in range(1, len(k_coords)):
        dk = np.sqrt(sum((k_coords[i][j] - k_coords[i-1][j])**2 for j in range(3)))
        k_dist.append(k_dist[-1] + dk)

    return k_coords, bands, np.array(k_dist)


def find_high_symmetry_points(k_coords, k_dist):
    """Detect high-symmetry point positions from direction changes in k-path."""
    hs_positions = [0.0]
    for i in range(1, len(k_coords) - 1):
        v1 = np.array(k_coords[i]) - np.array(k_coords[i-1])
        v2 = np.array(k_coords[i+1]) - np.array(k_coords[i])
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 > 1e-10 and n2 > 1e-10:
            v1 /= n1
            v2 /= n2
            if np.linalg.norm(v1 - v2) > 0.01:
                hs_positions.append(k_dist[i])
    hs_positions.append(k_dist[-1])
    return hs_positions


def compute_vbm_cbm(bands, fermi_ev):
    """
    Compute VBM and CBM using the SCF Fermi energy as the dividing line.

    For spin-polarised systems the .dat file contains all bands from both
    spin channels. We use E_F to separate occupied from unoccupied states:
      VBM = max energy of any band that is everywhere <= E_F  (highest occupied)
      CBM = min energy of any band that is anywhere  >= E_F  (lowest unoccupied)

    More robustly: across all k-points collect the single highest energy
    below E_F and the single lowest energy above E_F.
    """
    all_below = []  # all eigenvalues below Fermi
    all_above = []  # all eigenvalues above Fermi

    for energies in bands.values():
        for e in energies:
            if e <= fermi_ev:
                all_below.append(e)
            else:
                all_above.append(e)

    vbm = max(all_below) if all_below else None
    cbm = min(all_above) if all_above else None

    if vbm is not None and cbm is not None:
        gap = cbm - vbm   # negative = overlap (metallic); positive = real gap
    else:
        gap = None

    return vbm, cbm, gap


def plot_bands(dat_file, compound_name, output_file=None):
    """
    Plot band structure with correct Fermi level and VBM/CBM markers.
    Bands are shifted so E_F = 0 on the y-axis.
    """
    print(f"\n  Plotting: {compound_name}")

    # --- Fermi energy ---
    fermi = FERMI_FROM_SCF.get(compound_name)
    if fermi is None:
        print(f"  WARNING: No SCF Fermi energy for {compound_name}. Add it to FERMI_FROM_SCF.")
        return
    print(f"  Fermi (from SCF): {fermi:.4f} eV")

    # --- Read band data ---
    k_coords, bands, k_dist = read_band_dat(dat_file)
    if not bands:
        print(f"  ERROR: No bands found in {dat_file}")
        return
    print(f"  k-points: {len(k_coords)},  bands: {len(bands)}")

    # --- VBM / CBM / gap ---
    vbm, cbm, gap = compute_vbm_cbm(bands, fermi)
    if gap is not None:
        print(f"  VBM: {vbm:.3f} eV  ({vbm - fermi:+.3f} eV rel. to E_F)")
        print(f"  CBM: {cbm:.3f} eV  ({cbm - fermi:+.3f} eV rel. to E_F)")
        print(f"  Gap: {gap:.3f} eV  ({'metallic overlap' if gap < 0 else 'semiconductor'})")

    hs_pos = find_high_symmetry_points(k_coords, k_dist)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot bands shifted so Fermi = 0
    for band_energies in bands.values():
        # shifted = [e - fermi for e in band_energies]
        # ax.plot(k_dist, shifted, 'b-', linewidth=0.8, alpha=0.7)
        ax.plot(k_dist, band_energies, 'b-', linewidth=0.8, alpha=0.7)

    # High-symmetry vertical lines
    for pos in hs_pos:
        ax.axvline(pos, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)

    # # Fermi level at 0
    # ax.axhline(0, color='red', linestyle='--', linewidth=1.5,
    #            label='$E_F$ (from SCF)', alpha=0.9, zorder=10)

    ax.axhline(fermi, color='red', linestyle='--', linewidth=1.5,
           label=f'$E_F$ = {fermi:.3f} eV', alpha=0.9, zorder=10)

    # # VBM and CBM lines (shifted)
    # if vbm is not None and cbm is not None:
    #     vbm_shifted = vbm - fermi
    #     cbm_shifted = cbm - fermi
    #     ax.axhline(vbm_shifted, color='darkorange', linestyle=':',
    #                linewidth=1.2, label=f'VBM = {vbm_shifted:+.3f} eV', alpha=0.8)
    #     ax.axhline(cbm_shifted, color='purple', linestyle=':',
    #                linewidth=1.2, label=f'CBM = {cbm_shifted:+.3f} eV', alpha=0.8)
    #     # Shade the gap region
    #     if gap is not None:
    #         color = 'lightcoral' if gap < 0 else 'lightgreen'
    #         ax.axhspan(vbm_shifted, cbm_shifted, alpha=0.15, color=color)

    ax.axhline(vbm, color='darkorange', linestyle=':',
           linewidth=1.2, label=f'VBM = {vbm:.3f} eV', alpha=0.8)
    ax.axhline(cbm, color='purple', linestyle=':',
            linewidth=1.2, label=f'CBM = {cbm:.3f} eV', alpha=0.8)
    if gap is not None:
        color = 'lightcoral' if gap < 0 else 'lightgreen'
        ax.axhspan(vbm, cbm, alpha=0.15, color=color)

    # Axes and labels
    ax.set_xticks(hs_pos)
    ax.set_xticklabels(KPOINT_LABELS[:len(hs_pos)])
    # ax.set_ylabel('$E - E_F$ (eV)', fontsize=13, fontweight='bold')
    ax.set_ylabel('$E$ (eV)', fontsize=13, fontweight='bold')
    ax.set_title(compound_name.replace('_', ' '), fontsize=14, fontweight='bold')
    ax.set_xlim(k_dist[0], k_dist[-1])
    # ax.set_ylim(-6, 6)   # ±6 eV shifted around Fermi — adjust if needed
    ax.set_ylim(fermi - 6, fermi + 6)
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.2, axis='y')

    # Gap annotation
    if gap is not None:
        label = f'Gap = {gap:.3f} eV' if gap >= 0 else f'Overlap = {gap:.3f} eV'
        ax.text(0.02, 0.02, label, transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved: {output_file}")
    plt.close()


def main():
    print("=" * 70)
    print("  FIXED BAND STRUCTURE PLOTTER")
    print("  Bands shifted to E_F = 0 | Fermi from SCF | Correct VBM/CBM")
    print("=" * 70)

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
    os.makedirs('fixed_bands', exist_ok=True)

    for dat_file, name in dat_files:
        if Path(dat_file).exists():
            plot_bands(dat_file, name, f'fixed_bands/{name}_bands.png')
        else:
            print(f"\n  MISSING: {dat_file}")

    print("\n" + "=" * 70)
    print("  Done. Plots saved to fixed_bands/")
    print("=" * 70)
    print("""
  What the plots now show:
    - All bands shifted so E_F = 0 (y-axis is E - E_F)
    - Red dashed line = Fermi level (correct SCF value)
    - Orange dotted line = VBM (highest occupied state)
    - Purple dotted line = CBM (lowest unoccupied state)
    - Green shading = positive gap (semiconductor)
    - Red shading = negative gap (spin-channel overlap / metallic)
    - Gap or Overlap value shown in corner
""")


if __name__ == "__main__":
    main()
