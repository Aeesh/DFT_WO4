#!/usr/bin/env python3
"""
Plot DOS and Extract Band Gaps
Simple, clear analysis of your DOS files
"""

import numpy as np
import matplotlib.pyplot as plt
import glob
import os

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11

# def extract_fermi_and_gap_from_dos_stale(dos_file):
#     """
#     Extract Fermi energy and band gap from DOS file
#     """
#     # Read header to get Fermi energy
#     with open(dos_file, 'r') as f:
#         header = f.readline()

#     # Extract EFermi
#     e_fermi = float(header.split('EFermi =')[1].split('eV')[0].strip())

#     # Load DOS data
#     data = np.loadtxt(dos_file, comments='#')
#     energy = data[:, 0]
#     dos_up = data[:, 1]
#     dos_down = data[:, 2]
#     dos_total = dos_up + dos_down

#     # Find band gap (where DOS is essentially zero)
#     threshold = 0.01  # states/eV threshold

#     # Find VBM (last energy below Fermi with significant DOS)
#     below_fermi = energy < e_fermi
#     vbm_idx = None
#     for i in range(len(energy)-1, -1, -1):
#         if below_fermi[i] and dos_total[i] > threshold:
#             vbm_idx = i
#             break

#     # Find CBM (first energy above Fermi with significant DOS)
#     above_fermi = energy > e_fermi
#     cbm_idx = None
#     for i in range(len(energy)):
#         if above_fermi[i] and dos_total[i] > threshold:
#             cbm_idx = i
#             break

#     if vbm_idx is None or cbm_idx is None:
#         return e_fermi, None, None, None

#     vbm = energy[vbm_idx]
#     cbm = energy[cbm_idx]
#     gap = cbm - vbm

#     return e_fermi, vbm, cbm, gap


def extract_fermi_and_gap_from_dos(dos_file):
    with open(dos_file, 'r') as f:
        header = f.readline()

    e_fermi = float(header.split('EFermi =')[1].split('eV')[0].strip())

    data = np.loadtxt(dos_file, comments='#')
    energy = data[:, 0]
    dos_up = data[:, 1]
    dos_down = data[:, 2]
    dos_total = dos_up + dos_down

    threshold = 0.01

    # Shift to Fermi level for searching
    e_shifted = energy - e_fermi

    # VBM: last point with energy < 0 (below Fermi) with significant DOS
    vbm = None
    for i in range(len(e_shifted) - 1, -1, -1):
        if e_shifted[i] < 0 and dos_total[i] > threshold:
            vbm = energy[i]
            break

    # CBM: first point with energy > 0 (above Fermi) with significant DOS
    cbm = None
    for i in range(len(e_shifted)):
        if e_shifted[i] > 0 and dos_total[i] > threshold:
            cbm = energy[i]
            break

    if vbm is None or cbm is None:
        return e_fermi, None, None, None

    gap = cbm - vbm
    return e_fermi, vbm, cbm, gap

def plot_dos(dos_file, output_name=None):
    """
    Plot DOS with band gap highlighted
    """
    # Extract info
    e_fermi, vbm, cbm, gap = extract_fermi_and_gap_from_dos(dos_file)

    # Load data
    data = np.loadtxt(dos_file, comments='#')
    energy = data[:, 0]
    dos_up = data[:, 1]
    dos_down = data[:, 2]

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot DOS
    ax.plot(energy, dos_up, 'b-', linewidth=1.5, label='Spin Up')
    ax.plot(energy, -dos_down, 'r-', linewidth=1.5, label='Spin Down')
    ax.axhline(0, color='black', linewidth=0.5)

    # Mark Fermi energy
    ax.axvline(e_fermi, color='green', linestyle='--', linewidth=2,
               label=f'$E_F$ = {e_fermi:.2f} eV', alpha=0.7)

    # Highlight band gap
    if gap is not None:
        ax.axvspan(vbm, cbm, alpha=0.2, color='yellow',
                   label=f'Band Gap = {gap:.3f} eV')
        ax.axvline(vbm, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
        ax.axvline(cbm, color='purple', linestyle=':', linewidth=1.5, alpha=0.7)

    # Formatting
    system_name = os.path.basename(dos_file).replace('.dos', '')
    ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Density of States (states/eV)', fontsize=13, fontweight='bold')
    ax.set_title(f'Density of States: {system_name}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(e_fermi - 5, e_fermi + 5)  # Plot ±5 eV around Fermi

    plt.tight_layout()

    if output_name:
        plt.savefig(output_name, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_name}")
    else:
        plt.savefig(f'{system_name}_DOS.png', dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {system_name}_DOS.png")

    plt.close()

    return e_fermi, vbm, cbm, gap

def analyze_all_dos(dos_directory='tmp'):
    """
    Analyze all .dos files in directory
    """
    # dos_files = glob.glob(os.path.join(dos_directory, '*.dos'))
    dos_files = glob.glob(os.path.join(dos_directory, '**', '*.dos'), recursive=True)

    if not dos_files:
        print("❌ No .dos files found!")
        return

    output_dir = 'dos_plot_results'
    os.makedirs(output_dir, exist_ok=True)

    print("="*80)
    print(" DOS ANALYSIS - BAND GAP EXTRACTION")
    print("="*80)

    results = []

    for dos_file in sorted(dos_files):
        system_name = os.path.basename(dos_file).replace('.dos', '')
        print(f"\n📊 Analyzing: {system_name}")

        # e_fermi, vbm, cbm, gap = plot_dos(dos_file])
        output_name = os.path.join(output_dir, f'{system_name}_DOS.png')
        e_fermi, vbm, cbm, gap = plot_dos(dos_file, output_name=output_name)

        if gap is not None:
            print(f"   E_Fermi: {e_fermi:.3f} eV")
            print(f"   VBM: {vbm:.3f} eV")
            print(f"   CBM: {cbm:.3f} eV")
            print(f"   ✅ Band Gap: {gap:.3f} eV")

            results.append({
                'System': system_name,
                'E_Fermi': e_fermi,
                'VBM': vbm,
                'CBM': cbm,
                'Gap': gap
            })
        else:
            print(f"   ⚠️  Could not determine band gap")

    # Print summary
    print("\n" + "="*80)
    print(" SUMMARY TABLE")
    print("="*80)
    print(f"\n{'System':<20} {'E_Fermi (eV)':<14} {'VBM (eV)':<12} {'CBM (eV)':<12} {'Gap (eV)':<10}")
    print("-"*80)

    for r in results:
        print(f"{r['System']:<20} {r['E_Fermi']:>13.3f} {r['VBM']:>11.3f} {r['CBM']:>11.3f} {r['Gap']:>9.3f}")

    # Save to file
    # with open('DOS_BAND_GAPS.txt', 'w') as f:
    with open(os.path.join(output_dir, 'DOS_BAND_GAPS.txt'), 'w') as f:
        f.write("="*80 + "\n")
        f.write(" BAND GAPS FROM DOS ANALYSIS\n")
        f.write("="*80 + "\n\n")
        f.write(f"{'System':<20} {'E_Fermi (eV)':<14} {'VBM (eV)':<12} {'CBM (eV)':<12} {'Gap (eV)':<10}\n")
        f.write("-"*80 + "\n")
        for r in results:
            f.write(f"{r['System']:<20} {r['E_Fermi']:>13.3f} {r['VBM']:>11.3f} {r['CBM']:>11.3f} {r['Gap']:>9.3f}\n")

    print(f"\n✅ Saved: DOS_BAND_GAPS.txt")

    # Save CSV
    # with open('DOS_BAND_GAPS.csv', 'w') as f:
    with open(os.path.join(output_dir, 'DOS_BAND_GAPS.csv'), 'w') as f:
        f.write("System,E_Fermi_eV,VBM_eV,CBM_eV,BandGap_eV\n")
        for r in results:
            f.write(f"{r['System']},{r['E_Fermi']:.4f},{r['VBM']:.4f},{r['CBM']:.4f},{r['Gap']:.4f}\n")

    print(f"✅ Saved: DOS_BAND_GAPS.csv\n")

    return results

if __name__ == "__main__":
    print("\n🔬 DOS Analysis and Band Gap Extraction\n")
    results = analyze_all_dos()

    if results:
        print("="*80)
        print(" ✅ SUCCESS!")
        print("="*80)
        print("\nGenerated:")
        print("  • Individual DOS plots for each system")
        print("  • DOS_BAND_GAPS.txt - Summary table")
        print("  • DOS_BAND_GAPS.csv - Data for further analysis")
        print("\nALL DONE! 🎉")
    else:
        print("\n❌ No results - check that .dos files are in current directory")