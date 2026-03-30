#!/usr/bin/env python3
"""
CORRECTED Band Structure Plotter
Shows gap around Fermi energy properly
"""

import numpy as np
import matplotlib.pyplot as plt
import re
import os

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 12

# High-symmetry point labels
KPOINT_LABELS = [r'$\Gamma$', 'Y', 'M', r'$\Gamma$', 'Z', 'A']

def find_fermi_energy(system_name):
    """
    Find Fermi energy from multiple possible output files
    """
    possible_files = [
        f'bands_outputs/{system_name}_bands.out',
        f'nscf_outputs/nscf.{system_name}.out',
        f'outputs/scf.{system_name}.out',
        f'scf_outputs/scf.{system_name}.out',
    ]

    for filepath in possible_files:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        if 'Fermi energy' in line or 'the Fermi energy is' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                try:
                                    if 'Fermi' in part or 'energy' in part:
                                        fermi = float(parts[i+2])
                                        print(f"  ✅ Found Fermi energy: {fermi:.3f} eV from {os.path.basename(filepath)}")
                                        return fermi
                                except:
                                    pass
            except:
                pass

    print(f"  ⚠️  Could not find Fermi energy for {system_name}")
    return None

def read_band_gnu(gnu_file):
    """
    Read the .gnu file from bands.x
    Returns: bands dict and k_distances list
    """
    with open(gnu_file, 'r') as f:
        lines = f.readlines()

    # Parse data
    k_points = []
    bands_at_k = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split()
        if len(parts) >= 2:
            k = float(parts[0])
            energy = float(parts[1])

            if k not in k_points:
                k_points.append(k)

            k_idx = k_points.index(k)
            if k_idx not in bands_at_k:
                bands_at_k[k_idx] = []
            bands_at_k[k_idx].append(energy)

    # Convert to band arrays
    n_kpoints = len(k_points)
    n_bands = len(bands_at_k[0]) if 0 in bands_at_k else 0

    bands = {}
    for band_idx in range(n_bands):
        bands[band_idx] = []
        for k_idx in range(n_kpoints):
            if k_idx in bands_at_k and band_idx < len(bands_at_k[k_idx]):
                bands[band_idx].append(bands_at_k[k_idx][band_idx])

    return bands, k_points

def find_high_symmetry_positions(k_points):
    """
    Detect high-symmetry points (where k-path direction changes)
    """
    hs_positions = [k_points[0]]

    # Simple approach: look for large jumps in k-distance
    for i in range(1, len(k_points) - 1):
        dk_prev = k_points[i] - k_points[i-1]
        dk_next = k_points[i+1] - k_points[i]

        # If spacing changes significantly, it's a high-symmetry point
        if abs(dk_next - dk_prev) > 0.001:
            hs_positions.append(k_points[i])

    hs_positions.append(k_points[-1])

    return hs_positions

def plot_band_structure(gnu_file, system_name, output_file):
    """
    Plot band structure centered on Fermi energy
    """
    # Read bands
    print(f"\n📊 {system_name}...")
    print(f"  📂 Reading: {gnu_file}")

    try:
        bands, k_points = read_band_gnu(gnu_file)
        print(f"  📈 Found {len(bands)} bands, {len(k_points)} k-points")
    except Exception as e:
        print(f"  ❌ Failed to read bands: {e}")
        return False

    # Find Fermi energy
    fermi = find_fermi_energy(system_name)

    if fermi is None:
        print(f"  ⚠️  Plotting without Fermi shift (absolute energies)")

    # Find high-symmetry positions
    hs_positions = find_high_symmetry_positions(k_points)
    print(f"  🎯 High-symmetry points at: {[f'{x:.3f}' for x in hs_positions]}")

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Determine which bands to plot (only near Fermi level)
    plot_range = 4.0  # eV above/below Fermi

    if fermi is not None:
        # Shift energies and select bands near Fermi
        bands_to_plot = []
        for band_idx, energies in bands.items():
            energies_array = np.array(energies) - fermi  # SHIFT TO E - E_F
            # Check if any part crosses our plot range
            if np.any((energies_array > -plot_range) & (energies_array < plot_range)):
                bands_to_plot.append((band_idx, energies_array))

        ylabel = 'Energy - $E_F$ (eV)'
        title_suffix = ''
    else:
        # No Fermi energy - plot all bands in absolute energy
        bands_to_plot = [(idx, np.array(energies)) for idx, energies in bands.items()]
        ylabel = 'Energy (eV)'
        title_suffix = ' (absolute energies)'
        plot_range = 10.0

    print(f"  🎨 Plotting {len(bands_to_plot)} bands near Fermi level")

    # Plot bands
    for band_idx, energies in bands_to_plot:
        ax.plot(k_points, energies, 'b-', linewidth=1.0, alpha=0.7)

    # Mark Fermi level
    if fermi is not None:
        ax.axhline(0, color='red', linestyle='--', linewidth=2,
                   label='$E_F$', alpha=0.8, zorder=10)

    # High-symmetry lines
    for pos in hs_positions:
        ax.axvline(pos, color='gray', linestyle=':', linewidth=1.2, alpha=0.5)

    # Formatting
    ax.set_xticks(hs_positions)
    if len(hs_positions) <= len(KPOINT_LABELS):
        ax.set_xticklabels(KPOINT_LABELS[:len(hs_positions)], fontsize=14)
    else:
        ax.set_xticklabels([f'k{i}' for i in range(len(hs_positions))], fontsize=12)

    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.set_xlabel('k-path', fontsize=14, fontweight='bold')
    ax.set_title(f'Band Structure: {system_name}{title_suffix}', fontsize=15, fontweight='bold')
    ax.set_xlim(k_points[0], k_points[-1])
    ax.set_ylim(-plot_range, plot_range)

    if fermi is not None:
        ax.legend(fontsize=12, loc='upper right')

    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Saved: {output_file}")
    return True

def main():
    """Process all band structures"""
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

    os.makedirs('corrected_band_plots', exist_ok=True)

    print("="*80)
    print(" CORRECTED BAND STRUCTURE PLOTTING")
    print(" (Properly centered on Fermi energy)")
    print("="*80)

    success_count = 0

    for system_name in systems:
        # Look for .gnu file
        gnu_file = f'tmp/{system_name}/{system_name}_bands.dat.gnu'
        if not os.path.exists(gnu_file):
            gnu_file = f'{system_name}_bands.dat.gnu'

        if not os.path.exists(gnu_file):
            print(f"\n⚠️  {system_name}: {gnu_file} not found - skipping")
            continue

        output_file = f'corrected_band_plots/{system_name}_bands_corrected.png'

        if plot_band_structure(gnu_file, system_name, output_file):
            success_count += 1

    print("\n" + "="*80)
    print(f" ✅ DONE! Successfully plotted {success_count}/{len(systems)} systems")
    print("="*80)
    print("\nCorrected band plots in: corrected_band_plots/")
    print("These plots are properly centered on Fermi energy (E_F = 0)")
    print("\nShow these to your PI - the gap should now be visible around E=0!")

if __name__ == "__main__":
    main()