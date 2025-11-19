#!/usr/bin/env python3
"""
Automated binary (A,B)WO4 QE input generator.
Preserves unary starting_magnetization, Hubbard U, cell, and positions.
Generates 50:50 binaries in a new folder, ready to run.
"""

import os
import itertools
import re

def read_unary_file(file_path):
    """Read unary QE input and return lines, starting_mags, hubbard_lines"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    starting_mags = []
    hubbard_lines = []
    in_system = False
    in_hubbard = False
    
    for line in lines:
        if "&SYSTEM" in line.upper():
            in_system = True
        if "HUBBARD" in line.upper():
            in_hubbard = True
            in_system = False
        if in_system and "starting_magnetization" in line.lower():
            starting_mags.append(line)
        if in_hubbard:
            if line.strip() == "" or line.strip().startswith("&"):
                in_hubbard = False
            elif line.strip().upper().startswith("U "):
                hubbard_lines.append(line)
    return lines, starting_mags, hubbard_lines

def replace_half_metal(lines, metalA, metalB):
    """Replace half of metalA atoms with metalB, preserving AFM labels"""
    new_lines = []
    positions_started = False
    metal_indices = []

    for idx, line in enumerate(lines):
        if line.strip().upper().startswith("ATOMIC_POSITIONS"):
            positions_started = True
            new_lines.append(line)
            continue
        if positions_started:
            if line.strip() == "" or line.strip().startswith("&") or line.strip().upper().startswith(("K_POINTS", "CELL_PARAMETERS")):
                positions_started = False
                new_lines.append(line)
                continue
            # Atom label
            atom_label = line.strip().split()[0]
            base_label = re.sub(r'\d', '', atom_label)
            if base_label == metalA:
                metal_indices.append(idx)
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    n_metal = len(metal_indices)
    n_replace = n_metal // 2
    for i, idx in enumerate(metal_indices[n_replace:]):
        parts = new_lines[idx].strip().split()
        label = parts[0]
        # Preserve AFM label
        if '1' in label:
            new_label = metalB + '1'
        elif '2' in label:
            new_label = metalB + '2'
        else:
            new_label = metalB
        parts[0] = new_label
        new_lines[idx] = "  ".join(parts) + "\n"
    
    return new_lines

def merge_starting_mags(magsA, magsB):
    """Combine and deduplicate starting_magnetization lines"""
    combined = magsA + magsB
    seen_species = set()
    deduped = []
    for line in combined:
        species_match = re.search(r'starting_magnetization\(\d+\)\s*=\s*([0-9\.\-]+)', line)
        if species_match:
            species_value = species_match.group(0)
            if species_value not in seen_species:
                deduped.append(line)
                seen_species.add(species_value)
        else:
            deduped.append(line)
    return deduped

def create_binary(fileA, fileB, output_dir="binary_input"):
    os.makedirs(output_dir, exist_ok=True)
    
    linesA, magsA, hubA = read_unary_file(fileA)
    linesB, magsB, hubB = read_unary_file(fileB)
    
    basenameA = re.sub(r'\d','',os.path.basename(fileA).split('.')[1])
    basenameB = re.sub(r'\d','',os.path.basename(fileB).split('.')[1])
    
    binary_lines = replace_half_metal(linesA, basenameA, basenameB)
    
    merged_mags = merge_starting_mags(magsA, magsB)
    merged_hub = hubA + hubB
    
    final_lines = []
    in_system = False
    for line in binary_lines:
        final_lines.append(line)
        if "&SYSTEM" in line.upper():
            in_system = True
        elif in_system and line.strip().startswith("/"):
            # Insert starting_mags before the end of &SYSTEM
            final_lines = final_lines[:-1] + merged_mags + ["/\n"]
            in_system = False
    
    # Add HUBBARD section at the end
    final_lines.append("\nHUBBARD {ortho-atomic}\n")
    final_lines.extend(merged_hub)
    
    output_file = os.path.join(output_dir, f"scf.{basenameA}{basenameB}WO4.in")
    with open(output_file, 'w') as f:
        f.writelines(final_lines)
    
    print(f"✅ Created: {output_file}")
    return output_file

def generate_all_binaries(input_dir="inputs", metals=['Mn','Fe','Co','Ni','Cu','Zn']):
    pairs = list(itertools.combinations(metals, 2))
    all_files = []
    for a, b in pairs:
        fileA = os.path.join(input_dir, f"scf.{a}WO4.in")
        fileB = os.path.join(input_dir, f"scf.{b}WO4.in")
        if not os.path.exists(fileA) or not os.path.exists(fileB):
            print(f"⚠️ Missing {fileA} or {fileB}, skipping.")
            continue
        try:
            out_file = create_binary(fileA, fileB)
            all_files.append(out_file)
        except Exception as e:
            print(f"❌ Error creating binary {a},{b}: {e}")
    print(f"\n✓ All binaries generated in '{output_dir}'")
    return all_files

if __name__ == "__main__":
    generate_all_binaries(input_dir="inputs", metals=['Mn','Fe','Co','Ni','Cu','Zn'])
