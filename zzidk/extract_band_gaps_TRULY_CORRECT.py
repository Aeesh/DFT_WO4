#!/usr/bin/env python3
"""
CORRECT APPROACH FOR SPIN-POLARIZED BAND GAP:
For each k-point and each spin:
  - Find gap within that spin channel
Then take minimum gap across all k-points and spins
"""

import re
import numpy as np
from pathlib import Path

def extract_band_gap_correct(filepath):
    """
    Correctly extract band gap for spin-polarized system
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Get number of electrons
        nelec_match = re.search(r'number of electrons\s*=\s*(\d+\.\d+)', content)
        if not nelec_match:
            print(f"  ❌ Could not find electron count")
            return None

        n_electrons = float(nelec_match.group(1))
        print(f"\n  Analyzing {filepath.name}:")
        print(f"    Total electrons: {n_electrons}")

        # Split into SPIN UP and SPIN DOWN
        spin_up_match = re.search(r'------ SPIN UP ------------(.*)------ SPIN DOWN ----------', content, re.DOTALL)
        spin_down_match = re.search(r'------ SPIN DOWN ----------(.*?)(?=highest occupied|the Fermi energy is|Writing all to output|$)', content, re.DOTALL)

        if not spin_up_match or not spin_down_match:
            print(f"    ❌ Could not find SPIN UP/DOWN sections")
            return None

        spin_up_text = spin_up_match.group(1)
        spin_down_text = spin_down_match.group(1)

        # Process each spin channel to find gap WITHIN that channel
        gap_up, details_up = process_spin_for_gap(spin_up_text, "UP")
        gap_down, details_down = process_spin_for_gap(spin_down_text, "DOWN")

        if gap_up is None or gap_down is None:
            print(f"    ❌ Failed to extract gaps")
            return None

        # The overall band gap is the MINIMUM of the two spin channels
        if gap_up < gap_down:
            gap = gap_up
            vbm = details_up['vbm']
            cbm = details_up['cbm']
            gap_type = "Spin-UP"
        else:
            gap = gap_down
            vbm = details_down['vbm']
            cbm = details_down['cbm']
            gap_type = "Spin-DOWN"

        print(f"    ")
        print(f"    Spin UP gap:   {gap_up:.3f} eV")
        print(f"    Spin DOWN gap: {gap_down:.3f} eV")
        print(f"    ")
        print(f"    ✅ Minimum gap: {gap:.3f} eV (from {gap_type} channel)")
        print(f"    ✅ VBM: {vbm:.3f} eV, CBM: {cbm:.3f} eV")

        if gap < 0.1:
            print(f"    ⚠️  Very small gap - near metallic!")

        if gap > 5:
            print(f"    ⚠️  Very large gap - please verify")

        return {
            'gap': gap,
            'vbm': vbm,
            'cbm': cbm,
            'gap_up': gap_up,
            'gap_down': gap_down,
            'gap_type': gap_type,
            'n_electrons': n_electrons
        }

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_spin_for_gap(spin_text, label):
    """
    Find the band gap WITHIN a single spin channel
    Returns (gap, {vbm, cbm})
    """
    # Find all k-point blocks
    kpoint_blocks = re.findall(
        r'k\s*=\s*([\d\.\s-]+)\s*\(\s*(\d+)\s*PWs\)\s*bands\s*\(ev\):(.*?)occupation numbers\s+(.*?)(?=\n\s*k\s*=|\Z)',
        spin_text,
        re.DOTALL
    )

    if not kpoint_blocks:
        print(f"      No k-points found in SPIN {label}")
        return None, None

    print(f"      SPIN {label}: Found {len(kpoint_blocks)} k-points")

    min_gap = float('inf')
    best_vbm = None
    best_cbm = None

    for k_coords, n_pw, band_text, occ_text in kpoint_blocks:
        # Parse energies
        energies = []
        for val in band_text.split():
            try:
                energies.append(float(val))
            except:
                continue

        # Parse occupations
        occs = []
        for val in occ_text.split():
            try:
                occs.append(float(val))
            except:
                continue

        # Find VBM and CBM at THIS k-point
        vbm_k = -float('inf')
        cbm_k = float('inf')

        for e, occ in zip(energies, occs):
            if occ > 0.5:  # Occupied
                vbm_k = max(vbm_k, e)
            elif occ < 0.5:  # Unoccupied
                cbm_k = min(cbm_k, e)

        # Calculate gap at this k-point
        if vbm_k != -float('inf') and cbm_k != float('inf'):
            gap_k = cbm_k - vbm_k

            # Keep track of minimum gap
            if gap_k < min_gap:
                min_gap = gap_k
                best_vbm = vbm_k
                best_cbm = cbm_k

    if min_gap == float('inf'):
        return None, None

    return min_gap, {'vbm': best_vbm, 'cbm': best_cbm}


def analyze_all(nscf_dir='nscf_outputs'):
    """Analyze all NSCF files"""
    nscf_path = Path(nscf_dir)

    if not nscf_path.exists():
        print(f"❌ Directory {nscf_dir} not found")
        return None

    print("="*80)
    print(" CORRECT BAND GAP EXTRACTION FOR SPIN-POLARIZED SYSTEMS")
    print(" (Finds gap WITHIN each spin channel, then takes minimum)")
    print("="*80)

    compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
    mag_types = ['FM', 'AFM']

    results = {}

    for compound in compounds:
        for mag in mag_types:
            filename = f"nscf.{compound}_{mag}.out"
            filepath = nscf_path / filename

            if filepath.exists():
                print(f"\n{'='*80}")
                print(f"  {compound} ({mag})")
                print('='*80)

                data = extract_band_gap_correct(filepath)

                if data:
                    results[f"{compound}_{mag}"] = data

    # Print summary
    print("\n" + "="*80)
    print(" COMPLETE SUMMARY")
    print("="*80)

    header = f"\n{'Compound':<12} {'Config':<6} {'Gap (eV)':<10} {'Gap Type':<12} {'VBM (eV)':<10} {'CBM (eV)':<10}"
    print(header)
    print("-"*80)

    for compound in compounds:
        for mag in mag_types:
            key = f"{compound}_{mag}"
            if key in results:
                d = results[key]
                print(f"{compound:<12} {mag:<6} {d['gap']:>8.3f}   {d['gap_type']:<12} {d['vbm']:>8.3f}   {d['cbm']:>8.3f}")
            else:
                print(f"{compound:<12} {mag:<6} {'FAILED':>8}   {'---':<12} {'---':>8}   {'---':>8}")

    # FM vs AFM comparison
    print("\n" + "="*80)
    print(" FM vs AFM BAND GAP COMPARISON")
    print("="*80)
    print(f"\n{'Compound':<12} {'FM Gap (eV)':<13} {'AFM Gap (eV)':<13} {'ΔGap (eV)':<13}")
    print("-"*80)

    for compound in compounds:
        fm_key = f"{compound}_FM"
        afm_key = f"{compound}_AFM"

        if fm_key in results and afm_key in results:
            fm_gap = results[fm_key]['gap']
            afm_gap = results[afm_key]['gap']
            delta = afm_gap - fm_gap
            print(f"{compound:<12} {fm_gap:>11.3f}   {afm_gap:>11.3f}   {delta:>+11.3f}")

    # Save results
    with open('BAND_GAPS_CORRECT.txt', 'w') as f:
        f.write("="*80 + "\n")
        f.write(" CORRECT BAND GAP ANALYSIS - SPIN-POLARIZED DFT+U\n")
        f.write(" Binary (Mn,X)WO₄ Tungstates\n")
        f.write("="*80 + "\n\n")

        f.write("METHODOLOGY:\n")
        f.write("  - Spin-polarized calculations (nspin=2)\n")
        f.write("  - For each k-point in each spin channel:\n")
        f.write("      gap(k,spin) = CBM(k,spin) - VBM(k,spin)\n")
        f.write("  - Overall band gap = min(gap) across all k and spins\n\n")

        f.write("="*80 + "\n")
        f.write("RESULTS:\n")
        f.write("="*80 + "\n\n")

        f.write(f"{'Compound':<12} {'Config':<6} {'Gap (eV)':<10} {'VBM (eV)':<10} {'CBM (eV)':<10}\n")
        f.write("-"*80 + "\n")

        for compound in compounds:
            for mag in mag_types:
                key = f"{compound}_{mag}"
                if key in results:
                    d = results[key]
                    f.write(f"{compound:<12} {mag:<6} {d['gap']:>8.3f}   {d['vbm']:>8.3f}   {d['cbm']:>8.3f}\n")

        f.write("\n" + "="*80 + "\n")
        f.write("FM vs AFM COMPARISON:\n")
        f.write("="*80 + "\n\n")

        f.write(f"{'Compound':<12} {'FM (eV)':<10} {'AFM (eV)':<10} {'Δ (eV)':<10}\n")
        f.write("-"*80 + "\n")

        for compound in compounds:
            fm_key = f"{compound}_FM"
            afm_key = f"{compound}_AFM"

            if fm_key in results and afm_key in results:
                fm_gap = results[fm_key]['gap']
                afm_gap = results[afm_key]['gap']
                delta = afm_gap - fm_gap
                f.write(f"{compound:<12} {fm_gap:>8.3f}  {afm_gap:>8.3f}  {delta:>+8.3f}\n")

    print(f"\n✅ Saved: BAND_GAPS_CORRECT.txt")

    # Save CSV
    with open('BAND_GAPS_CORRECT.csv', 'w') as f:
        f.write("Compound,Config,BandGap_eV,VBM_eV,CBM_eV,Gap_Type\n")
        for compound in compounds:
            for mag in mag_types:
                key = f"{compound}_{mag}"
                if key in results:
                    d = results[key]
                    f.write(f"{compound},{mag},{d['gap']:.4f},{d['vbm']:.4f},{d['cbm']:.4f},{d['gap_type']}\n")

    print(f"✅ Saved: BAND_GAPS_CORRECT.csv\n")

    return results


if __name__ == "__main__":
    print("\n🔬 CORRECT Band Gap Extraction - Spin-Resolved Analysis\n")
    results = analyze_all()

    if results and len(results) > 0:
        print("="*80)
        print(" ✅ SUCCESS!")
        print("="*80)
        print("\nGenerated files:")
        print("  • BAND_GAPS_CORRECT.txt")
        print("  • BAND_GAPS_CORRECT.csv")
        print("\nNext: Update create_plots_for_PI.py to use BAND_GAPS_CORRECT.csv")
    else:
        print("\n❌ Failed to extract band gaps")