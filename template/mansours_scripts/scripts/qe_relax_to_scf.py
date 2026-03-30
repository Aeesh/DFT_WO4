import sys
import re

def extract_final_geometry(outfile_path):
    """Extracts the final CELL_PARAMETERS and ATOMIC_POSITIONS from the output."""
    with open(outfile_path, 'r') as f:
        lines = f.readlines()

    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if "Begin final coordinates" in line:
            start_idx = i
        if "End final coordinates" in line:
            end_idx = i

    if start_idx == -1 or end_idx == -1:
        print(f"Error: Could not find 'Begin final coordinates' in {outfile_path}.")
        sys.exit(1)

    # Extract the chunk
    final_block = lines[start_idx+1 : end_idx]
    
    new_geometry = []
    for line in final_block:
        # Filter out informational lines
        if "new" in line or "density" in line or "volume" in line: 
            continue
        new_geometry.append(line)
        
    return "".join(new_geometry)

def create_scf_input(infile_path, outfile_path, geometry_block):
    with open(infile_path, 'r') as f:
        content = f.read()

    # 1. Change calculation type (Catches both 'relax' and 'vc-relax')
    content = re.sub(r"calculation\s*=\s*['\"](?:vc-)?relax['\"]", "calculation = 'scf'", content, flags=re.IGNORECASE)
    
    # 2. Completely remove IONS and CELL blocks to prevent clutter
    content = re.sub(r"&IONS[\s\S]*?/", "", content, flags=re.IGNORECASE)
    content = re.sub(r"&CELL[\s\S]*?/", "", content, flags=re.IGNORECASE)

    # 3. ROBUST DELETION of old geometry
    # We explicitly list QE card names so the regex doesn't stop at atom names like "Mn1"
    qe_cards = r"(ATOMIC_SPECIES|ATOMIC_POSITIONS|K_POINTS|HUBBARD|CELL_PARAMETERS|&|\Z)"
    
    # Remove old ATOMIC_POSITIONS and its coordinates
    pattern_pos = r"ATOMIC_POSITIONS[\s\S]*?(?=\n\s*" + qe_cards + ")"
    content = re.sub(pattern_pos, "", content, flags=re.IGNORECASE)
    
    # Remove old CELL_PARAMETERS and its data (if present)
    pattern_cell = r"CELL_PARAMETERS[\s\S]*?(?=\n\s*" + qe_cards + ")"
    content = re.sub(pattern_cell, "", content, flags=re.IGNORECASE)

    # Clean up excess empty lines left behind by the deletion
    content = re.sub(r"\n{3,}", "\n\n", content)

    # 4. INSERT NEW GEOMETRY SAFELY
    # The correct place for geometry is immediately before K_POINTS
    header = "! --- Updated Geometry from Relaxation ---\n"
    formatted_geometry = header + geometry_block.strip() + "\n\n"

    if re.search(r"K_POINTS", content, flags=re.IGNORECASE):
        # Inject right before K_POINTS
        content = re.sub(r"(K_POINTS)", formatted_geometry + r"\1", content, count=1, flags=re.IGNORECASE)
    else:
        # Fallback just in case K_POINTS is missing
        content += "\n\n" + formatted_geometry

    # 5. Write new file
    new_filename = infile_path.replace("relax", "scf")
    if new_filename == infile_path:
        new_filename = infile_path + ".scf"

    with open(new_filename, 'w') as f:
        f.write(content.strip() + "\n")
    
    print(f"Success! Created {new_filename}")

if __name__ == "__main__":
    materials = [
        "CoWO4", 
        "CuWO4", 
        "FeWO4", 
        "MnWO4", 
        "NiWO4", 
        "ZnWO4"
    ]
    for material in materials:
        out_file = f"/trace/group/dabo/mansouro/unary/{material}/relax.{material}.out"
        in_file = f"/trace/group/dabo/mansouro/unary/{material}/relax.{material}.in"
        
        try:
            final_geo = extract_final_geometry(out_file)
            create_scf_input(in_file, out_file, final_geo)
        except Exception as e:
            print(f"Skipping {material} due to error: {e}")