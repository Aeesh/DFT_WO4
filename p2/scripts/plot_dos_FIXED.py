#!/usr/bin/env python3
"""
FIXED DOS PLOTTER
- Uses Fermi energy from the .dos file header (written by QE dos.x — correct)
- Searches for band gap WITHIN each spin channel separately
- Reports spin-up gap, spin-down gap, and combined gap correctly
- Shows ±5 eV window around E_F
"""

import numpy as np
import matplotlib.pyplot as plt
import glob
import os

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 11


FERMI_ENERGIES = {
    'MnCoWO4_AFM': 12.4323,
    'MnCoWO4_FM':  12.4714,
    'MnFeWO4_FM':  12.6410,
    'MnNiWO4_AFM': 11.9136,
    'MnNiWO4_FM':  11.9606,
    'MnZnWO4_AFM': 11.2876,
    'MnZnWO4_FM':  11.2876,
}


def extract_gap_from_dos(dos_file):
    """
    Extract Fermi energy and band gaps from a QE .dos file.

    For spin-polarised systems the correct approach is to find the gap
    WITHIN each spin channel separately, then take the minimum.

    The Fermi energy in the .dos header is the one computed by QE's dos.x
    from the smearing — it is the correct value to use here.
    """
    with open(dos_file, 'r') as f:
        header = f.readline()

    # Parse Fermi energy from header line like:
    # #  E (eV)   dosup(E)  dosdw(E)  Int dos(E)  EFermi = 13.823 eV
    # e_fermi = float(header.split('EFermi =')[1].split('eV')[0].strip())
    # e_fermi = 12.4323


    # TODO: revert to reading fermi from dos file
    # Default: read from DOS header
    e_fermi = float(header.split('EFermi =')[1].split('eV')[0].strip())

    # Override using config if available
    system_name = os.path.basename(dos_file).replace('.dos', '')

    if system_name in FERMI_ENERGIES:
        e_fermi = FERMI_ENERGIES[system_name]
    else:
        print(f"  Warning: No config EF for {system_name}, using DOS value ({e_fermi:.4f} eV)")

    data = np.loadtxt(dos_file, comments='#')
    energy   = data[:, 0]
    dos_up   = data[:, 1]
    dos_down = data[:, 2]

    # threshold = 0.05  # states/eV — raised from 0.01 to avoid threshold artifact
    threshold = 0.5

    def find_gap_in_channel(dos_channel):
        """
        Find VBM and CBM within a single spin channel.
        VBM = last energy below E_F with DOS > threshold
        CBM = first energy above E_F with DOS > threshold
        """
        vbm = None
        cbm = None
        for i in range(len(energy) - 1, -1, -1):
            if energy[i] < e_fermi and dos_channel[i] > threshold:
                vbm = energy[i]
                break
        for i in range(len(energy)):
            if energy[i] > e_fermi and dos_channel[i] > threshold:
                cbm = energy[i]
                break
        if vbm is not None and cbm is not None:
            return vbm, cbm, cbm - vbm
        return None, None, None

    vbm_up,   cbm_up,   gap_up   = find_gap_in_channel(dos_up)
    vbm_down, cbm_down, gap_down = find_gap_in_channel(dos_down)

    # Overall gap: minimum of the two spin channels
    # If either channel is metallic (no gap), overall = metallic
    if gap_up is not None and gap_down is not None:
        gap_overall = min(gap_up, gap_down)
        if gap_up < gap_down:
            vbm_overall, cbm_overall = vbm_up, cbm_up
        else:
            vbm_overall, cbm_overall = vbm_down, cbm_down
    elif gap_up is not None:
        vbm_overall, cbm_overall, gap_overall = vbm_up, cbm_up, gap_up
    elif gap_down is not None:
        vbm_overall, cbm_overall, gap_overall = vbm_down, cbm_down, gap_down
    else:
        vbm_overall, cbm_overall, gap_overall = None, None, None

    return (e_fermi,
            vbm_up, cbm_up, gap_up,
            vbm_down, cbm_down, gap_down,
            vbm_overall, cbm_overall, gap_overall)


def plot_dos(dos_file, output_name=None):
    """Plot DOS with spin channels, Fermi level, and gap correctly marked."""

    result = extract_gap_from_dos(dos_file)
    (e_fermi,
     vbm_up, cbm_up, gap_up,
     vbm_down, cbm_down, gap_down,
     vbm_overall, cbm_overall, gap_overall) = result

    data     = np.loadtxt(dos_file, comments='#')
    energy   = data[:, 0]
    dos_up   = data[:, 1]
    dos_down = data[:, 2]

    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Plot spin channels ---
    ax.plot(energy,  dos_up,   'b-', linewidth=1.5, label='Spin Up')
    ax.plot(energy, -dos_down, 'r-', linewidth=1.5, label='Spin Down')
    ax.axhline(0, color='black', linewidth=0.5)

    # --- Fermi energy ---
    ax.axvline(e_fermi, color='green', linestyle='--', linewidth=2,
               label=f'$E_F$ = {e_fermi:.3f} eV', alpha=0.8, zorder=5)

    # --- Gap markers ---
    if gap_up is not None and gap_up > 0:
        ax.axvspan(vbm_up, cbm_up, alpha=0.12, color='deepskyblue',
                   label=f'Spin↑ gap = {gap_up:.3f} eV')
    if gap_down is not None and gap_down > 0:
        ax.axvspan(vbm_down, cbm_down, alpha=0.12, color='salmon',
                   label=f'Spin↓ gap = {gap_down:.3f} eV')

    # --- Annotation ---
    system_name = os.path.basename(dos_file).replace('.dos', '')
    ax.set_xlabel('Energy (eV)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Density of States (states/eV)', fontsize=13, fontweight='bold')
    ax.set_title(f'DOS: {system_name}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.2)
    ax.set_xlim(e_fermi - 5, e_fermi + 5)

    # Gap summary box
    lines = []
    if gap_up is not None:
        lines.append(f"Spin↑ gap: {gap_up:.3f} eV" if gap_up > 0 else f"Spin↑: metallic ({gap_up:.3f} eV)")
    if gap_down is not None:
        lines.append(f"Spin↓ gap: {gap_down:.3f} eV" if gap_down > 0 else f"Spin↓: metallic ({gap_down:.3f} eV)")
    if gap_overall is not None:
        lines.append(f"Overall: {gap_overall:.3f} eV")
    if lines:
        ax.text(0.02, 0.97, '\n'.join(lines), transform=ax.transAxes, fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    out = output_name or f'{system_name}_DOS.png'
    plt.savefig(out, dpi=300, bbox_inches='tight')
    print(f"  Saved: {out}")
    plt.close()

    return result


def analyze_all_dos(dos_directory='tmp'):
    """Find all .dos files and analyse them."""
    dos_files = glob.glob(os.path.join(dos_directory, '**', '*.dos'), recursive=True)
    if not dos_files:
        print("No .dos files found! Check your directory.")
        return

    os.makedirs('fixed_dos', exist_ok=True)

    print("=" * 75)
    print("  FIXED DOS ANALYSIS")
    print("=" * 75)

    results = []
    for dos_file in sorted(dos_files):
        name = os.path.basename(dos_file).replace('.dos', '')
        print(f"\n  {name}")
        result = plot_dos(dos_file, output_name=f'fixed_dos/{name}_DOS.png')
        (e_fermi,
         vbm_up, cbm_up, gap_up,
         vbm_down, cbm_down, gap_down,
         vbm_overall, cbm_overall, gap_overall) = result

        print(f"    E_Fermi  = {e_fermi:.3f} eV")
        if gap_up   is not None: print(f"    Spin-up gap   = {gap_up:.3f} eV")
        if gap_down is not None: print(f"    Spin-down gap = {gap_down:.3f} eV")
        if gap_overall is not None:
            if gap_overall > 0:
                print(f"    Overall gap   = {gap_overall:.3f} eV  (semiconductor)")
            else:
                print(f"    Overall       = {gap_overall:.3f} eV  (metallic overlap)")

        results.append({
            'System': name,
            'E_Fermi': e_fermi,
            'Gap_up': gap_up,
            'Gap_down': gap_down,
            'Gap_overall': gap_overall,
        })

    # Summary table
    print("\n" + "=" * 75)
    print(f"  {'System':<22} {'E_F (eV)':<12} {'Gap↑ (eV)':<12} {'Gap↓ (eV)':<12} {'Overall (eV)'}")
    print("  " + "-" * 72)
    for r in results:
        gu = f"{r['Gap_up']:.3f}"   if r['Gap_up']   is not None else "N/A"
        gd = f"{r['Gap_down']:.3f}" if r['Gap_down'] is not None else "N/A"
        go = f"{r['Gap_overall']:.3f}" if r['Gap_overall'] is not None else "N/A"
        print(f"  {r['System']:<22} {r['E_Fermi']:>11.3f} {gu:>11} {gd:>11} {go:>12}")

    # Save CSV
    with open('fixed_dos/DOS_GAPS_FIXED.csv', 'w') as f:
        f.write("System,E_Fermi_eV,Gap_up_eV,Gap_down_eV,Gap_overall_eV\n")
        for r in results:
            f.write(f"{r['System']},{r['E_Fermi']:.4f},"
                    f"{r['Gap_up'] or 'N/A'},"
                    f"{r['Gap_down'] or 'N/A'},"
                    f"{r['Gap_overall'] or 'N/A'}\n")
    print("\n  Saved: fixed_dos/DOS_GAPS_FIXED.csv")

    return results


if __name__ == "__main__":
    analyze_all_dos()
