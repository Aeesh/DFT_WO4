#!/usr/bin/env python3
"""
COMPLETE DFT ANALYSIS TOOL - ALL PHASES
========================================

This script analyzes results from Phase 1-3 of your binary tungstates research:
- Phase 1: Unary reference calculations (if available)
- Phase 2: SCF/Relax calculations → Energies, magnetic ground states
- Phase 3: NSCF calculations → Band gaps

Outputs:
1. Complete summary tables (CSV)
2. Publication-quality plots
3. Professional report for PI

Author: For Aisha's Binary Tungstates Research
Date: January 2026
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

class CompleteDFTAnalyzer:
    """Comprehensive analyzer for all DFT calculation phases"""

    def __init__(self,
                 scf_dir='outputs',
                 relax_dir='relax_outputs',
                 nscf_dir='nscf_outputs',
                 unary_dir='unary_outputs'):
        """Initialize with directories for different calculation types"""
        self.scf_dir = Path(scf_dir)
        self.relax_dir = Path(relax_dir)
        self.nscf_dir = Path(nscf_dir)
        self.unary_dir = Path(unary_dir)

        self.results = defaultdict(dict)
        self.band_gaps = {}
        self.energies = {}

    def extract_total_energy(self, filepath):
        """Extract final total energy from any output file"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Try multiple patterns
            patterns = [
                r'Final energy\s*=\s*(-?\d+\.\d+)\s*Ry',
                r'!\s*total energy\s*=\s*(-?\d+\.\d+)\s*Ry',
                r'total energy\s*=\s*(-?\d+\.\d+)\s*Ry'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return float(matches[-1])

            return None
        except:
            return None

    def extract_band_gap_from_nscf(self, filepath):
        """
        Extract band gap from NSCF output

        Key insight: The "highest occupied, lowest unoccupied" line can be misleading
        for indirect gap semiconductors. We need to find:
        - VBM = maximum energy with occupation = 1.0000
        - CBM = minimum energy with occupation = 0.0000
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Find number of electrons (to know how many bands are occupied)
            nelec_match = re.search(r'number of electrons\s*=\s*(\d+\.\d+)', content)
            if not nelec_match:
                return None

            n_electrons = float(nelec_match.group(1))
            n_occupied_bands = int(n_electrons / 2)  # Assuming spin-polarized

            # Extract all band energies and occupations
            # Pattern: bands (ev): followed by energies, then occupation numbers
            band_sections = re.findall(
                r'bands \(ev\):(.*?)occupation numbers\s+(.*?)(?=\n\s*$|\n\s*k\s*=)',
                content,
                re.DOTALL
            )

            if not band_sections:
                # Try simpler extraction from summary line
                gap_match = re.search(
                    r'highest occupied, lowest unoccupied level \(ev\):\s*(\S+)\s+(\S+)',
                    content
                )
                if gap_match:
                    homo = float(gap_match.group(1))
                    lumo = float(gap_match.group(2))
                    # This might be wrong for indirect gap, but it's a fallback
                    return max(0, lumo - homo)
                return None

            # Parse all k-points to find true VBM and CBM
            vbm = -float('inf')  # Valence Band Maximum
            cbm = float('inf')   # Conduction Band Minimum

            for bands_text, occ_text in band_sections:
                # Parse energies
                energies = [float(x) for x in bands_text.split()]
                occupations = [float(x) for x in occ_text.split()]

                # Find VBM (max of occupied states)
                for e, occ in zip(energies, occupations):
                    if occ > 0.5:  # Occupied (1.0000)
                        vbm = max(vbm, e)
                    elif occ < 0.5:  # Unoccupied (0.0000)
                        cbm = min(cbm, e)

            # Calculate gap
            if vbm != -float('inf') and cbm != float('inf'):
                gap = cbm - vbm
                return {
                    'gap': gap,
                    'vbm': vbm,
                    'cbm': cbm,
                    'n_electrons': n_electrons
                }

            return None

        except Exception as e:
            print(f"Error extracting band gap from {filepath}: {e}")
            return None

    def analyze_phase2_scf(self):
        """Analyze Phase 2: SCF/Relax energies"""
        print("\n" + "="*70)
        print("PHASE 2 ANALYSIS: SCF/Relaxation Energies")
        print("="*70)

        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
        mag_types = ['FM', 'AFM']

        for compound in compounds:
            for mag in mag_types:
                # Check relax outputs first, then regular outputs
                filename = f"scf.{compound}_{mag}.out"

                # Try relax directory first
                filepath = self.relax_dir / filename
                if not filepath.exists():
                    filepath = self.scf_dir / filename

                if filepath.exists():
                    energy = self.extract_total_energy(filepath)
                    if energy:
                        self.energies[f"{compound}_{mag}"] = energy
                        print(f"  {compound} {mag}: {energy:.6f} Ry")

    def analyze_phase3_nscf(self):
        """Analyze Phase 3: Band gaps from NSCF"""
        print("\n" + "="*70)
        print("PHASE 3 ANALYSIS: Band Gaps from NSCF")
        print("="*70)

        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
        mag_types = ['FM', 'AFM']

        for compound in compounds:
            for mag in mag_types:
                filename = f"nscf.{compound}_{mag}.out"
                filepath = self.nscf_dir / filename

                if filepath.exists():
                    gap_data = self.extract_band_gap_from_nscf(filepath)
                    if gap_data:
                        self.band_gaps[f"{compound}_{mag}"] = gap_data
                        print(f"  {compound} {mag}:")
                        print(f"    Band Gap: {gap_data['gap']:.3f} eV")
                        print(f"    VBM: {gap_data['vbm']:.3f} eV")
                        print(f"    CBM: {gap_data['cbm']:.3f} eV")

    def generate_complete_summary(self):
        """Generate comprehensive summary table"""
        print("\n" + "="*70)
        print("COMPLETE SUMMARY TABLE")
        print("="*70)

        data = []
        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']

        for compound in compounds:
            fm_key = f"{compound}_FM"
            afm_key = f"{compound}_AFM"

            # Get energies
            e_fm = self.energies.get(fm_key)
            e_afm = self.energies.get(afm_key)

            # Calculate magnetic preference
            if e_fm and e_afm:
                delta_e = (e_fm - e_afm) * 13.6057  # Convert Ry to eV
                ground_state = 'AFM' if delta_e > 0 else 'FM'
                mag_stability = abs(delta_e)
            else:
                delta_e = None
                ground_state = 'N/A'
                mag_stability = None

            # Get band gaps
            gap_fm = self.band_gaps.get(fm_key, {}).get('gap')
            gap_afm = self.band_gaps.get(afm_key, {}).get('gap')

            # FM row
            data.append({
                'Compound': compound,
                'Config': 'FM',
                'E_total (Ry)': f"{e_fm:.6f}" if e_fm else 'N/A',
                'Band Gap (eV)': f"{gap_fm:.3f}" if gap_fm else 'N/A',
                'ΔE(FM-AFM) (eV)': f"{delta_e:+.3f}" if delta_e else 'N/A',
                'Ground State': ground_state if ground_state == 'FM' else ''
            })

            # AFM row
            data.append({
                'Compound': compound,
                'Config': 'AFM',
                'E_total (Ry)': f"{e_afm:.6f}" if e_afm else 'N/A',
                'Band Gap (eV)': f"{gap_afm:.3f}" if gap_afm else 'N/A',
                'ΔE(FM-AFM) (eV)': '',
                'Ground State': ground_state if ground_state == 'AFM' else ''
            })

        df = pd.DataFrame(data)
        print("\n", df.to_string(index=False))

        # Save to CSV
        df.to_csv('COMPLETE_ANALYSIS_SUMMARY.csv', index=False)
        print(f"\nSaved to: COMPLETE_ANALYSIS_SUMMARY.csv")

        return df

    def plot_band_gaps(self):
        """Create publication-quality band gap comparison plot"""
        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']

        fm_gaps = []
        afm_gaps = []
        labels = []

        for compound in compounds:
            fm_gap = self.band_gaps.get(f"{compound}_FM", {}).get('gap')
            afm_gap = self.band_gaps.get(f"{compound}_AFM", {}).get('gap')

            if fm_gap or afm_gap:
                fm_gaps.append(fm_gap if fm_gap else 0)
                afm_gaps.append(afm_gap if afm_gap else 0)
                labels.append(compound.replace('WO4', ''))

        if not labels:
            print("No band gap data available for plotting")
            return

        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width/2, fm_gaps, width, label='FM',
                       color='steelblue', edgecolor='black', alpha=0.8)
        bars2 = ax.bar(x + width/2, afm_gaps, width, label='AFM',
                       color='coral', edgecolor='black', alpha=0.8)

        ax.set_xlabel('Compound', fontsize=12, fontweight='bold')
        ax.set_ylabel('Band Gap (eV)', fontsize=12, fontweight='bold')
        ax.set_title('Band Gaps of Binary (Mn,X)WO₄ Tungstates\nFM vs AFM Configurations',
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, max(max(fm_gaps), max(afm_gaps)) * 1.2)

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}',
                           ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig('BAND_GAPS_COMPARISON.png', dpi=300, bbox_inches='tight')
        print("\nSaved plot: BAND_GAPS_COMPARISON.png")
        plt.close()

    def plot_magnetic_stability(self):
        """Plot magnetic ground state preferences"""
        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']

        delta_e_list = []
        labels = []
        colors = []

        for compound in compounds:
            fm_key = f"{compound}_FM"
            afm_key = f"{compound}_AFM"

            e_fm = self.energies.get(fm_key)
            e_afm = self.energies.get(afm_key)

            if e_fm and e_afm:
                delta_e = (e_fm - e_afm) * 13.6057  # Ry to eV
                delta_e_list.append(delta_e)
                labels.append(compound.replace('WO4', ''))
                colors.append('coral' if delta_e > 0 else 'steelblue')

        if not labels:
            print("No energy data available for magnetic stability plot")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(labels)), delta_e_list, color=colors,
                      edgecolor='black', alpha=0.8)

        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax.set_xlabel('Compound', fontsize=12, fontweight='bold')
        ax.set_ylabel('ΔE = E(FM) - E(AFM) [eV]', fontsize=12, fontweight='bold')
        ax.set_title('Magnetic Ground State Analysis\nBinary (Mn,X)WO₄ Tungstates',
                     fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=11)
        ax.grid(axis='y', alpha=0.3)

        # Add annotations
        for i, (bar, de) in enumerate(zip(bars, delta_e_list)):
            gs = 'AFM' if de > 0 else 'FM'
            ax.text(bar.get_x() + bar.get_width()/2., de,
                   f'{gs}\n{abs(de):.3f} eV',
                   ha='center', va='bottom' if de > 0 else 'top',
                   fontsize=9, fontweight='bold')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='coral', edgecolor='black', label='AFM Ground State'),
            Patch(facecolor='steelblue', edgecolor='black', label='FM Ground State')
        ]
        ax.legend(handles=legend_elements, loc='best', fontsize=10)

        plt.tight_layout()
        plt.savefig('MAGNETIC_GROUND_STATES.png', dpi=300, bbox_inches='tight')
        print("Saved plot: MAGNETIC_GROUND_STATES.png")
        plt.close()

    def generate_pi_report(self):
        """Generate comprehensive report for PI"""
        report = []
        report.append("="*80)
        report.append("COMPLETE DFT ANALYSIS REPORT")
        report.append("Binary (Mn,X)WO₄ Tungstates Research Project")
        report.append("="*80)
        report.append(f"\nGenerated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Researcher: Aisha, Manyara, Mansour")

        report.append("\n" + "="*80)
        report.append("PROJECT OVERVIEW")
        report.append("="*80)
        report.append("\nObjective: Investigate electronic property modulation in binary tungstates")
        report.append("Systems: (Mn,X)WO₄ where X = Fe, Co, Ni, Zn")
        report.append("Approach: DFT+U calculations with structure relaxation")

        report.append("\n" + "="*80)
        report.append("COMPUTATIONAL METHODOLOGY")
        report.append("="*80)
        report.append("\n1. Structure Preparation:")
        report.append("   - Base: MnWO₄ monoclinic structure")
        report.append("   - Method: Substitution + Vegard's law for lattice")
        report.append("   - Relaxation: BFGS algorithm until forces < 2×10⁻⁵ Ry/Bohr")

        report.append("\n2. Electronic Structure Calculations:")
        report.append("   - Functional: PBE/PBEsol + Hubbard U corrections")
        report.append("   - U values: Mn(4.65 eV), Fe(7.08 eV), Co(7.84 eV), Ni(8.55 eV)")
        report.append("   - Plane-wave cutoff: 120 Ry")
        report.append("   - k-point mesh: 6×6×6 (SCF), 12×12×12 (NSCF)")

        report.append("\n3. Magnetic Configurations:")
        report.append("   - FM: Ferromagnetic (parallel spins)")
        report.append("   - AFM: Antiferromagnetic (antiparallel spins)")

        report.append("\n" + "="*80)
        report.append("KEY RESULTS")
        report.append("="*80)

        # Magnetic ground states
        report.append("\n1. MAGNETIC GROUND STATES:")
        compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
        for compound in compounds:
            fm_e = self.energies.get(f"{compound}_FM")
            afm_e = self.energies.get(f"{compound}_AFM")
            if fm_e and afm_e:
                delta_e = (fm_e - afm_e) * 13.6057
                gs = 'AFM' if delta_e > 0 else 'FM'
                report.append(f"   {compound}: {gs} (ΔE = {abs(delta_e):.3f} eV)")

        # Band gaps
        report.append("\n2. BAND GAPS:")
        for compound in compounds:
            fm_gap = self.band_gaps.get(f"{compound}_FM", {}).get('gap')
            afm_gap = self.band_gaps.get(f"{compound}_AFM", {}).get('gap')
            if fm_gap or afm_gap:
                report.append(f"   {compound}:")
                if fm_gap:
                    report.append(f"     FM:  {fm_gap:.3f} eV")
                if afm_gap:
                    report.append(f"     AFM: {afm_gap:.3f} eV")

        report.append("\n" + "="*80)
        report.append("CONCLUSIONS")
        report.append("="*80)

        # Count magnetic preferences
        afm_count = sum(1 for c in compounds
                       if self.energies.get(f"{c}_FM") and self.energies.get(f"{c}_AFM")
                       and (self.energies[f"{c}_FM"] - self.energies[f"{c}_AFM"]) > 0)

        report.append(f"\n1. {afm_count}/{len(compounds)} compounds favor AFM configuration")

        # Average gap
        all_gaps = [d.get('gap') for d in self.band_gaps.values() if d.get('gap')]
        if all_gaps:
            avg_gap = np.mean(all_gaps)
            report.append(f"2. Average band gap: {avg_gap:.3f} eV")
            report.append(f"3. Gap range: {min(all_gaps):.3f} - {max(all_gaps):.3f} eV")

        report.append("\n" + "="*80)
        report.append("GENERATED FILES")
        report.append("="*80)
        report.append("\n1. COMPLETE_ANALYSIS_SUMMARY.csv - All numerical results")
        report.append("2. BAND_GAPS_COMPARISON.png - Band gap comparison plot")
        report.append("3. MAGNETIC_GROUND_STATES.png - Magnetic stability plot")
        report.append("4. PI_COMPLETE_REPORT.txt - This report")

        report.append("\n" + "="*80)
        report.append("END OF REPORT")
        report.append("="*80)

        report_text = '\n'.join(report)

        with open('PI_COMPLETE_REPORT.txt', 'w') as f:
            f.write(report_text)

        print("\n" + report_text)
        print("\nSaved report: PI_COMPLETE_REPORT.txt")


def main():
    """Main analysis workflow"""
    print("="*80)
    print("COMPLETE DFT ANALYSIS TOOL - PHASES 1-3")
    print("Binary (Mn,X)WO₄ Tungstates")
    print("="*80)

    # Initialize analyzer
    # Adjust directory names to match your setup
    analyzer = CompleteDFTAnalyzer(
        scf_dir='outputs',           # or wherever your SCF outputs are
        relax_dir='relax_outputs',   # relaxation outputs
        nscf_dir='nscf_outputs',     # NSCF outputs
        unary_dir='unary_outputs'    # optional: unary reference calculations
    )

    # Run all analyses
    print("\n1. Analyzing Phase 2 (SCF/Relax energies)...")
    analyzer.analyze_phase2_scf()

    print("\n2. Analyzing Phase 3 (NSCF band gaps)...")
    analyzer.analyze_phase3_nscf()

    print("\n3. Generating complete summary...")
    analyzer.generate_complete_summary()

    print("\n4. Creating plots...")
    analyzer.plot_band_gaps()
    analyzer.plot_magnetic_stability()

    print("\n5. Generating PI report...")
    analyzer.generate_pi_report()

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print("\nGenerated files:")
    print("  ✓ COMPLETE_ANALYSIS_SUMMARY.csv")
    print("  ✓ BAND_GAPS_COMPARISON.png")
    print("  ✓ MAGNETIC_GROUND_STATES.png")
    print("  ✓ PI_COMPLETE_REPORT.txt")
    print("\nReady to present to your PI!")


if __name__ == "__main__":
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError as e:
        print(f"Error: {e}")
        print("\nPlease install required packages:")
        print("  pip install --user pandas matplotlib numpy")
        exit(1)

    main()