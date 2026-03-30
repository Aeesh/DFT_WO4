#!/usr/bin/env python3
"""
Extract band structure DIRECTLY from QE bands.out files
No need for bands.x!
"""

import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

# K-point labels
KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

def read_fermi_from_scf(scf_file):
    """Read Fermi energy from SCF output"""
    try:
        with open(scf_file, 'r') as f:
            for line in f:
                if 'the Fermi energy is' in line:
                    return float(line.split()[4])
    except:
        pass
    return None

def extract_bands_from_output(output_file):
    """
    Extract band data directly from pw.x bands calculation output
    Returns: k_points, bands_dict (for each spin)
    """
    with open(output_file, 'r') as f:
        content = f.read()

    # Check if spin-polarized
    is_spin = 'SPIN UP' in content

    # Split by spin if needed
    if is_spin:
        sections = {}
        spin_up = re.search(r'------ SPIN UP ------------(.*)------ SPIN DOWN ----------',
                           content, re.DOTALL)
        spin_down = re.search(r'------ SPIN DOWN ----------(.*?)(?=Writing all to output|PWSCF|$)',
                             content, re.DOTALL)

        if spin_up:
            sections['up'] = spin_up.group(1)
        if spin_down:
            sections['down'] = spin_down.group(1)
    else:
        sections = {'nospin': content}

    all_bands = {}
    k_points = []

    for spin_label, section in sections.items():
        # Find all k-point blocks
        kpoint_pattern = r'k\s*=\s*([\d\.\s-]+)\s*\(\s*\d+\s*PWs\)\s*bands\s*\(ev\):(.*?)(?=k\s*=|$)'
        matches = re.findall(kpoint_pattern, section, re.DOTALL)

        spin_bands = {}

        for k_coords_str, bands_str in matches:
            # Parse k-point coordinates
            k_coords = [float(x) for x in k_coords_str.split()]

            # Only store k-points once (from first spin)
            if spin_label == list(sections.keys())[0]:
                k_points.append(k_coords)

            # Parse band energies
            energies = []
            for line in bands_str.strip().split('\n'):
                if line.strip():
                    energies.extend([float(x) for x in line.split()])

            # Store by band index
            for band_idx, energy in enumerate(energies):
                if band_idx not in spin_bands:
                    spin_bands[band_idx] = []
                spin_bands[band_idx].append(energy)

        all_bands[spin_label] = spin_bands

    return k_points, all_bands

def calculate_k_distance(k_points):
    """Calculate distance along k-path"""
    k_dist = [0.0]
    for i in range(1, len(k_points)):
        dk = np.sqrt(sum((k_points[i][j] - k_points[i-1][j])**2 for j in range(3)))
        k_dist.append(k_dist[-1] + dk)
    return np.array(k_dist)

def find_high_symmetry_points(k_points, k_dist):
    """Find high-symmetry point positions"""
    hs_positions = [0.0]

    for i in range(1, len(k_points) - 1):
        v1 = np.array(k_points[i]) - np.array(k_points[i-1])
        v2 = np.array(k_points[i+1]) - np.array(k_points[i])

        v1 = v1 / (np.linalg.norm(v1) + 1e-10)
        v2 = v2 / (np.linalg.norm(v2) + 1e-10)

        if np.linalg.norm(v1 - v2) > 0.01:
            hs_positions.append(k_dist[i])

    hs_positions.append(k_dist[-1])
    return hs_positions

def plot_band_structure(output_file, fermi=None, save_file=None, title="Band Structure"):
    """Plot band structure from pw.x output"""

    print(f"\n📊 Processing {Path(output_file).name}...")

    # Extract data
    k_points, all_bands = extract_bands_from_output(output_file)

    if not k_points:
        print(f"  ❌ No k-points found!")
        return

    if not all_bands:
        print(f"  ❌ No bands found!")
        return

    print(f"  ✅ Found {len(k_points)} k-points")
    for spin_label, bands in all_bands.items():
        print(f"  ✅ {spin_label}: {len(bands)} bands")

    # Calculate k-distance
    k_dist = calculate_k_distance(k_points)
    hs_pos = find_high_symmetry_points(k_points, k_dist)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Determine if we should shift to Fermi level
    shift = fermi if fermi else 0.0
    ylabel = 'Energy - $E_F$ (eV)' if fermi else 'Energy (eV)'

    # Plot bands for each spin
    colors = {'up': 'blue', 'down': 'red', 'nospin': 'blue'}

    for spin_label, bands in all_bands.items():
        color = colors.get(spin_label, 'blue')
        alpha = 0.5 if len(all_bands) > 1 else 0.7

        for band_idx, energies in bands.items():
            ax.plot(k_dist, np.array(energies) - shift,
                   color=color, linewidth=0.8, alpha=alpha)

    # Fermi level
    if fermi:
        ax.axhline(0, color='red', linestyle='--', linewidth=1.5,
                  label='$E_F$', alpha=0.7, zorder=10)

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

    if fermi:
        ax.legend(fontsize=11, loc='upper right')

    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if save_file:
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved: {save_file}")
    else:
        plt.show()

    plt.close()

def main():
    """Process all uploaded band outputs"""
    print("="*80)
    print(" BAND STRUCTURE PLOTTER - DIRECT EXTRACTION")
    print(" (No bands.x needed!)")
    print("="*80)

    compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
    mags = ['FM', 'AFM']

    output_dir = Path('band_plots')
    output_dir.mkdir(exist_ok=True)

    # Look for band output files
    for compound in compounds:
        for mag in mags:
            # Try different possible locations
            possible_files = [
                f"bands_outputs/{compound}_{mag}_bands.out",
                f"{compound}_{mag}_bands.out",
                f"MnCoWO4_{mag}_bands.out"  # From your uploads
            ]

            band_file = None
            for pf in possible_files:
                if Path(pf).exists():
                    band_file = pf
                    break

            if not band_file:
                print(f"\n⚠️  {compound} ({mag}): Output file not found")
                continue

            # Get Fermi energy
            scf_file = f"scf_outputs/scf.{compound}_{mag}.out"
            fermi = read_fermi_from_scf(scf_file)

            if fermi:
                print(f"  ✅ Fermi energy: {fermi:.3f} eV")
            else:
                print(f"  ⚠️  Fermi energy not found (will plot without)")

            # Plot
            save_file = output_dir / f"{compound}_{mag}_bands.png"
            plot_band_structure(band_file, fermi, save_file, f"{compound} ({mag})")

    print("\n" + "="*80)
    print(" ✅ COMPLETE!")
    print("="*80)
    print(f"\nPlots saved in: {output_dir}/")

if __name__ == "__main__":
    main()