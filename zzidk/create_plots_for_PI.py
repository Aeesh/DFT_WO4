#!/usr/bin/env python3
"""
Create Publication-Quality Plots for PI Presentation
Shows band gaps and magnetic ground states
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Set publication style
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.linewidth'] = 1.5

def create_band_gap_comparison_plot(csv_file='BAND_GAPS_CORRECTED.csv'):
    """
    Create bar chart comparing FM vs AFM band gaps
    """
    # Read data
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"❌ Could not find {csv_file}")
        print("   Run extract_band_gaps_CORRECTED.py first!")
        return

    # Organize data
    compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']
    fm_gaps = []
    afm_gaps = []

    for compound in compounds:
        fm_row = df[(df['Compound'] == compound) & (df['Config'] == 'FM')]
        afm_row = df[(df['Compound'] == compound) & (df['Config'] == 'AFM')]

        fm_gap = fm_row['BandGap_eV'].values[0] if len(fm_row) > 0 else 0
        afm_gap = afm_row['BandGap_eV'].values[0] if len(afm_row) > 0 else 0

        fm_gaps.append(fm_gap)
        afm_gaps.append(afm_gap)

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(compounds))
    width = 0.35

    bars1 = ax.bar(x - width/2, fm_gaps, width, label='FM',
                   color='#3498db', edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, afm_gaps, width, label='AFM',
                   color='#e74c3c', edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Formatting
    ax.set_xlabel('Binary Tungstate Compound', fontsize=14, fontweight='bold')
    ax.set_ylabel('Band Gap (eV)', fontsize=14, fontweight='bold')
    ax.set_title('Band Gap Comparison: FM vs AFM Configurations\nBinary (Mn,X)WO₄ Tungstates',
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(compounds, fontsize=12)
    ax.legend(fontsize=12, loc='upper right', framealpha=0.9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max(max(fm_gaps), max(afm_gaps)) * 1.2)

    plt.tight_layout()
    plt.savefig('BAND_GAPS_COMPARISON_PLOT.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ Created: BAND_GAPS_COMPARISON_PLOT.png")


def create_combined_summary_plot(csv_file='BAND_GAPS_CORRECTED.csv',
                                 mag_csv='COMPLETE_ANALYSIS_SUMMARY.csv'):
    """
    Create comprehensive 2-panel plot showing:
    1. Band gaps (FM vs AFM)
    2. Magnetic ground states
    """
    # Read band gap data
    try:
        df_gaps = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"❌ Could not find {csv_file}")
        return

    # Read magnetic data
    try:
        df_mag = pd.read_csv(mag_csv)
    except FileNotFoundError:
        print(f"❌ Could not find {mag_csv}")
        return

    compounds = ['MnFeWO4', 'MnCoWO4', 'MnNiWO4', 'MnZnWO4']

    # Extract data
    fm_gaps = []
    afm_gaps = []
    mag_stability = []

    for compound in compounds:
        # Band gaps
        fm_row = df_gaps[(df_gaps['Compound'] == compound) & (df_gaps['Config'] == 'FM')]
        afm_row = df_gaps[(df_gaps['Compound'] == compound) & (df_gaps['Config'] == 'AFM')]

        fm_gap = fm_row['BandGap_eV'].values[0] if len(fm_row) > 0 else 0
        afm_gap = afm_row['BandGap_eV'].values[0] if len(afm_row) > 0 else 0

        fm_gaps.append(fm_gap)
        afm_gaps.append(afm_gap)

        # Magnetic stability
        mag_row_fm = df_mag[(df_mag[' Compound'] == compound) & (df_mag['Config'] == 'FM')]
        mag_row_afm = df_mag[(df_mag[' Compound'] == compound) & (df_mag['Config'] == 'AFM')]

        if len(mag_row_fm) > 0 and len(mag_row_afm) > 0:
            e_fm = mag_row_fm['E_total (Ry)'].values[0]
            e_afm = mag_row_afm['E_total (Ry)'].values[0]
            delta_e = (e_fm - e_afm) * 13.6057  # Convert to eV
            mag_stability.append(delta_e)
        else:
            mag_stability.append(0)

    # Create 2-panel figure
    fig = plt.figure(figsize=(16, 7))
    gs = fig.add_gridspec(1, 2, hspace=0.3, wspace=0.3)

    # Panel 1: Band Gaps
    ax1 = fig.add_subplot(gs[0, 0])
    x = np.arange(len(compounds))
    width = 0.35

    bars1 = ax1.bar(x - width/2, fm_gaps, width, label='FM',
                    color='#3498db', edgecolor='black', linewidth=1.5)
    bars2 = ax1.bar(x + width/2, afm_gaps, width, label='AFM',
                    color='#e74c3c', edgecolor='black', linewidth=1.5)

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax1.set_xlabel('Compound', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Band Gap (eV)', fontsize=13, fontweight='bold')
    ax1.set_title('(a) Electronic Band Gaps', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(compounds, fontsize=11)
    ax1.legend(fontsize=11, loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')

    # Panel 2: Magnetic Ground States
    ax2 = fig.add_subplot(gs[0, 1])

    colors = ['#e74c3c' if delta > 0.001 else '#3498db' if delta < -0.001 else '#95a5a6'
              for delta in mag_stability]
    labels = ['AFM' if delta > 0.001 else 'FM' if delta < -0.001 else 'Degenerate'
             for delta in mag_stability]

    bars = ax2.bar(x, [abs(d)*1000 for d in mag_stability], color=colors,
                   edgecolor='black', linewidth=1.5)

    for i, (bar, delta, label) in enumerate(zip(bars, mag_stability, labels)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{label}\n{abs(delta)*1000:.1f} meV',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax2.set_xlabel('Compound', fontsize=13, fontweight='bold')
    ax2.set_ylabel('|ΔE(FM-AFM)| (meV)', fontsize=13, fontweight='bold')
    ax2.set_title('(b) Magnetic Ground State Stability', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(compounds, fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')

    # Legend for panel 2
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#e74c3c', edgecolor='black', label='AFM Ground State'),
                      Patch(facecolor='#3498db', edgecolor='black', label='FM Ground State'),
                      Patch(facecolor='#95a5a6', edgecolor='black', label='Degenerate')]
    ax2.legend(handles=legend_elements, fontsize=10, loc='upper right')

    plt.suptitle('Electronic and Magnetic Properties of Binary (Mn,X)WO₄ Tungstates',
                fontsize=16, fontweight='bold', y=0.98)

    plt.savefig('COMPLETE_RESULTS_SUMMARY.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ Created: COMPLETE_RESULTS_SUMMARY.png")


def main():
    """Generate all plots for PI presentation"""
    print("="*80)
    print(" GENERATING PLOTS FOR PI PRESENTATION")
    print("="*80)

    print("\n1. Creating band gap comparison plot...")
    create_band_gap_comparison_plot()

    print("\n2. Creating combined summary plot...")
    create_combined_summary_plot()

    print("\n" + "="*80)
    print(" ✅ ALL PLOTS GENERATED!")
    print("="*80)
    print("\nFiles created:")
    print("  • BAND_GAPS_COMPARISON_PLOT.png - Band gaps only")
    print("  • COMPLETE_RESULTS_SUMMARY.png - Band gaps + magnetic states")
    print("\nThese plots are ready to show your PI!")


if __name__ == "__main__":
    main()