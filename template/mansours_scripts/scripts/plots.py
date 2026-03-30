import sys
import re
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ==========================================
# CONFIGURATION
# ==========================================
BASE_DIR = "/trace/group/dabo/mansouro/unary"
MATERIALS = ["CoWO4", "CuWO4", "FeWO4", "MnWO4", "NiWO4", "ZnWO4"]

# A larger color palette to cover all your transition metals
COLORS = {
    'Co': '#1f77b4', 'Cu': '#d62728', 'Fe': '#8c564b', 
    'Mn': '#9467bd', 'Ni': '#2ca02c', 'Zn': '#17becf', 
    'W': '#7f7f7f',  'O': '#ff7f0e',  'Total': 'black'
}

# ==========================================
# PARSING FUNCTIONS
# ==========================================

def get_fermi_energy(filepath):
    """Finds Fermi energy from an output file."""
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if "the Fermi energy is" in line:
                    return float(line.split()[-2])
                elif "highest occupied level" in line:
                    # Alternative string QE sometimes uses for insulators
                    return float(line.split()[-1])
    except FileNotFoundError:
        pass
    return None

def get_magnetization(filepath):
    """Extracts total and absolute magnetization."""
    total_mag, abs_mag = "N/A", "N/A"
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if "total magnetization" in line and "=" in line:
                    total_mag = float(line.split('=')[1].split()[0])
                if "absolute magnetization" in line and "=" in line:
                    abs_mag = float(line.split('=')[1].split()[0])
    except FileNotFoundError:
        pass
    return total_mag, abs_mag

def parse_bands_gnu(directory, prefix):
    """Parses .gnu files from bands.x, handling spin-polarized split files."""
    # Look for standard or spin-split files (e.g., .bands.dat.gnu or .bands.dat.1.gnu)
    pattern = f"{directory}/{prefix}.bands.dat*.gnu"
    files = glob.glob(pattern)
    
    all_bands = []
    for filepath in files:
        bands = []
        current_band = []
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip(): 
                    if current_band:
                        bands.append(np.array(current_band))
                        current_band = []
                else:
                    parts = line.split()
                    if len(parts) >= 2:
                        current_band.append([float(parts[0]), float(parts[1])])
            if current_band:
                bands.append(np.array(current_band))
        all_bands.extend(bands)
        
    return all_bands

def parse_pdos(directory, prefix, species_list, e_fermi):
    """Sums up PDOS files for each species, correctly handling spin."""
    pdos_data = {}
    energy_axis = None
    
    for species in species_list:
        # Matches files like: prefix.pdos_atm#1(Co)_wfc#1(d)
        pattern = f"{directory}/{prefix}.pdos_atm*({species})_wfc*"
        files = glob.glob(pattern)
        
        if not files:
            continue

        total_dos_species = None
        
        for file in files:
            try:
                data = np.loadtxt(file)
                
                # Capture energy axis on first successful read
                if energy_axis is None:
                    energy_axis = data[:, 0] - e_fermi
                
                # Check column count to handle Spin polarization
                if data.shape[1] >= 3:
                    # Spin-polarized: Col 1 is Up, Col 2 is Down. Sum them.
                    ldos = data[:, 1] + data[:, 2]
                else:
                    # Non-spin-polarized: Col 1 is total LDOS
                    ldos = data[:, 1]
                
                if total_dos_species is None:
                    total_dos_species = ldos
                else:
                    total_dos_species += ldos
                    
            except Exception as e:
                print(f"    Error reading {file}: {e}")

        if total_dos_species is not None:
            pdos_data[species] = total_dos_species

    return energy_axis, pdos_data

# ==========================================
# MAIN EXECUTION
# ==========================================

def process_material(material, base_dir):
    print(f"\n--- ANALYZING {material} ---")
    mat_dir = f"{base_dir}/{material}"
    
    # Dynamically extract species from name (e.g., 'FeWO4' -> ['Fe', 'W', 'O'])
    species_list = list(dict.fromkeys(re.findall(r'[A-Z][a-z]?', material)))
    
    # File Paths
    scf_out = f"{mat_dir}/scf.{material}.out"
    nscf_out = f"{mat_dir}/nscf.{material}.out"
    
    # 1. Get Fermi Energy
    e_fermi = get_fermi_energy(nscf_out)
    if e_fermi is None:
        e_fermi = get_fermi_energy(scf_out)
        
    if e_fermi is None:
        print("  -> Error: Could not find Fermi Energy. Skipping.")
        return

    print(f"  -> Fermi Energy: {e_fermi:.4f} eV")

    # 2. Get Magnetism
    tot_mag, abs_mag = get_magnetization(scf_out)
    print(f"  -> Total Mag: {tot_mag}, Abs Mag: {abs_mag}")

    # 3. Load Bands
    bands_data = parse_bands_gnu(mat_dir, material)
    if not bands_data:
        print("  -> Error: No bands data found. Did bands.x finish successfully?")
        return
    print(f"  -> Loaded {len(bands_data)} band segments.")

    # 4. Load PDOS
    eng_dos, pdos_dict = parse_pdos(mat_dir, material, species_list, e_fermi)
    if not pdos_dict:
        print("  -> Warning: No PDOS data found. Continuing with bands only.")

    # ==========================================
    # PLOTTING
    # ==========================================
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1], wspace=0.05)

    # --- LEFT PANEL: BAND STRUCTURE ---
    ax_bands = plt.subplot(gs[0])
    x_max = 0
    
    for band in bands_data:
        x = band[:, 0]
        y = band[:, 1] - e_fermi
        ax_bands.plot(x, y, color='black', linewidth=1.2, alpha=0.8)
        x_max = max(x_max, np.max(x))

    # Add vertical symmetry lines based on points where segments start
    if len(bands_data) > 0:
        segment_starts = [band[0, 0] for band in bands_data]
        for start_x in segment_starts:
            ax_bands.axvline(start_x, color='gray', linestyle='--', linewidth=0.5)

    ax_bands.axvline(x_max, color='gray', linestyle='--', linewidth=0.5)
    ax_bands.axhline(0, color='red', linestyle='--', linewidth=0.8, label="Fermi Level")

    # Band Gap Estimation (Robust for VBM slightly above 0 due to smearing)
    all_y = np.concatenate([band[:, 1] - e_fermi for band in bands_data])
    vbm_candidates = all_y[all_y <= 0.05]
    cbm_candidates = all_y[all_y > 0.05]

    if len(vbm_candidates) > 0 and len(cbm_candidates) > 0:
        vbm = np.max(vbm_candidates)
        cbm = np.min(cbm_candidates)
        gap = cbm - vbm
        print(f"  -> Estimated Band Gap: {gap:.4f} eV")
        ax_bands.text(x_max*0.05, 5, f"Gap $\\approx$ {gap:.2f} eV", fontsize=11, color='blue', bbox=dict(facecolor='white', alpha=0.8))
    else:
        print("  -> System appears metallic.")

    ax_bands.set_ylabel(r"Energy - $E_F$ (eV)", fontsize=12)
    ax_bands.set_ylim(-6, 6)
    ax_bands.set_xlim(0, x_max)
    ax_bands.set_title(f"{material} Band Structure", fontsize=14)
    ax_bands.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

    # --- RIGHT PANEL: PROJECTED DOS ---
    ax_dos = plt.subplot(gs[1])

    if eng_dos is not None and pdos_dict:
        total_dos = np.zeros_like(eng_dos)
        
        for species in species_list:
            if species in pdos_dict:
                dos = pdos_dict[species]
                color = COLORS.get(species, 'gray')
                ax_dos.plot(dos, eng_dos, label=species, color=color, linewidth=1.5)
                ax_dos.fill_betweenx(eng_dos, dos, 0, color=color, alpha=0.2)
                total_dos += dos

        ax_dos.plot(total_dos, eng_dos, color='black', linestyle=':', linewidth=1.2, label="Total")

    ax_dos.axhline(0, color='red', linestyle='--', linewidth=0.8)
    ax_dos.set_ylim(-6, 6)
    ax_dos.set_xlabel("DOS (states/eV)", fontsize=12)
    ax_dos.set_title("Projected DOS", fontsize=14)
    ax_dos.legend(loc='upper right', fontsize=10)
    ax_dos.set_yticklabels([]) 

    plt.tight_layout()
    out_png = f"{mat_dir}/{material}_Analysis.png"
    plt.savefig(out_png, dpi=300)
    print(f"  -> Success! Plot saved to {out_png}")
    plt.close(fig) # Prevent memory leaks

if __name__ == "__main__":
    for mat in MATERIALS:
        process_material(mat, BASE_DIR)