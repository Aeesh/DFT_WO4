import sys
import re
import math
import os
import json

def get_number_of_electrons(outfile_path):
    """Parses the SCF output to find the number of electrons."""
    electrons = 0.0
    try:
        with open(outfile_path, 'r') as f:
            for line in f:
                if "number of electrons" in line:
                    try:
                        parts = line.split('=')
                        electrons = float(parts[1].strip().split()[0])
                        return electrons
                    except:
                        continue
    except FileNotFoundError:
        print(f"  -> Error: {outfile_path} not found.")
    return 0.0

def get_kpath_from_scf(infile_path):
    """Extracts an existing band path from the SCF file if one is already defined."""
    with open(infile_path, 'r') as f:
        content = f.read()
        
    # Match K_POINTS that explicitly specify a path (crystal_b or tpiba_b)
    pattern = r"(K_POINTS\s*\{?\s*(?:crystal_b|tpiba_b)\s*\}?[\s\S]*?)(?=\n\s*(?:ATOMIC_SPECIES|ATOMIC_POSITIONS|CELL_PARAMETERS|HUBBARD|&|\Z))"
    match = re.search(pattern, content, flags=re.IGNORECASE)
    
    if match:
        return match.group(1).strip() + "\n"
    return None

def generate_kpoints_from_json(json_filepath):
    """Reads SeeK-path JSON and formats a K_POINTS {crystal_b} block."""
    with open(json_filepath, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("JSON file is empty or improperly formatted.")
            
    # Safeguard against empty placeholder JSONs
    if not data or 'kpoints_rel' not in data or 'path' not in data:
        raise ValueError("JSON is empty or missing SeeK-path data.")
        
    kpoints_rel = data['kpoints_rel']
    path_list = data['path']
    
    qe_path = []
    
    # Process the path segments into a linear list with correct weights
    for i, (start, end) in enumerate(path_list):
        if i == 0:
            qe_path.append({"label": start, "weight": 20})
        else:
            prev_end = path_list[i-1][1]
            if start != prev_end:
                # There is a jump in the path! Set previous node weight to 0
                qe_path[-1]["weight"] = 0
                qe_path.append({"label": start, "weight": 20})
                
        # Add the end of the current segment
        qe_path.append({"label": end, "weight": 20})
        
    # The very last point in the path must always have a weight of 0
    qe_path[-1]["weight"] = 0
    
    # Format the string for Quantum ESPRESSO
    lines = ["K_POINTS {crystal_b}"]
    lines.append(str(len(qe_path)))
    
    for node in qe_path:
        label = node["label"]
        coords = kpoints_rel[label]
        weight = node["weight"]
        # Format: kx ky kz weight ! Label
        lines.append(f"{coords[0]:10.6f}  {coords[1]:10.6f}  {coords[2]:10.6f}  {weight}  ! {label}")
        
    return "\n".join(lines) + "\n"

def create_bands_input(infile_path, outfile_path, electrons, kpoints_block):
    with open(infile_path, 'r') as f:
        content = f.read()

    # 1. Change calculation type
    content = re.sub(r"calculation\s*=\s*['\"](?:vc-)?(?:scf|relax)['\"]", "calculation = 'bands'", content, flags=re.IGNORECASE)
    
    # 2. Modify disk_io if it exists, otherwise leave it
    if "disk_io" in content:
        content = re.sub(r"disk_io\s*=\s*['\"]nowf['\"]", "disk_io = 'low'", content, flags=re.IGNORECASE)

    # 3. Calculate and Insert 'nbnd' (Number of Bands)
    if electrons > 0:
        nbnd = int(math.ceil(electrons / 2.0)) + 20
        # Prevent double-inserting nbnd if script is run multiple times
        if "nbnd" not in content:
            if "nspin" in content:
                content = re.sub(r"(nspin\s*=\s*\d+)", r"\1\n  nbnd = " + str(nbnd), content)
            else:
                content = re.sub(r"(/)", f"  nbnd = {nbnd}\n/", content, count=1)
        print(f"  -> Detected {electrons} electrons. Setting nbnd = {nbnd}")
    else:
        print("  -> Warning: Could not detect electron count. Please check 'nbnd' manually.")

    # 4. Replace K_POINTS block cleanly
    pattern = r"K_POINTS[\s\S]*?(?=\n\s*(?:ATOMIC_SPECIES|ATOMIC_POSITIONS|CELL_PARAMETERS|HUBBARD|&|\Z))"
    content = re.sub(pattern, kpoints_block, content, flags=re.IGNORECASE)

    # 5. Write the file
    bands_filename = infile_path.replace("scf", "bands")
    if bands_filename == infile_path:
        bands_filename = "bands." + os.path.basename(infile_path)

    with open(bands_filename, 'w') as f:
        f.write(content.strip() + "\n")
    
    print(f"  -> Success! Created {bands_filename}")

def create_bands_pp_input(scf_infile_path, pp_filepath, default_material):
    """Creates the bands.x post-processing input file by extracting prefix/outdir from SCF."""
    if os.path.exists(pp_filepath):
        return  # Do not overwrite if it already exists
        
    with open(scf_infile_path, 'r') as f:
        content = f.read()
        
    # Extract exact prefix and outdir used in the main calculation
    prefix_match = re.search(r"prefix\s*=\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE)
    outdir_match = re.search(r"outdir\s*=\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE)
    
    prefix = prefix_match.group(1) if prefix_match else default_material
    outdir = outdir_match.group(1) if outdir_match else './tmp/'
    
    pp_content = f"""&BANDS
  prefix  = '{prefix}'
  outdir  = '{outdir}'
  filband = '{prefix}.bands.dat'
/
"""
    with open(pp_filepath, 'w') as f:
        f.write(pp_content)
    print(f"  -> Success! Created post-processing file {os.path.basename(pp_filepath)}")

if __name__ == "__main__":
    materials = [
        "CoWO4", 
        "CuWO4", 
        "FeWO4", 
        "MnWO4", 
        "NiWO4", 
        "ZnWO4"
    ]
    
    base_dir = "/trace/group/dabo/mansouro/unary"
    
    for material in materials:
        print(f"\n--- Processing {material} ---")
        
        scf_in_file = f"{base_dir}/{material}/scf.{material}.in"
        scf_out_file = f"{base_dir}/{material}/scf.{material}.out"
        json_file = f"{base_dir}/{material}/{material}.json"
        pp_file = f"{base_dir}/{material}/{material}.bands.pp.in"
        
        if not os.path.exists(scf_in_file):
            print(f"  -> Skipping: Cannot find {scf_in_file}")
            continue

        try:
            # 1. PRIORITY: Check if SCF file already has a valid band path
            kpoints_text = get_kpath_from_scf(scf_in_file)
            
            if kpoints_text:
                print(f"  -> Found existing k-point path in SCF input. Using it.")
            else:
                # 2. FALLBACK: Read from JSON
                if not os.path.exists(json_file):
                    print(f"  -> JSON not found. Creating empty placeholder at {json_file}")
                    with open(json_file, 'w') as f:
                        json.dump({}, f)
                    print(f"  -> Skipping bands generation until JSON is populated or path is added to SCF.")
                    continue
                    
                print(f"  -> Reading k-path from {material}.json...")
                kpoints_text = generate_kpoints_from_json(json_file)
            
            # Fetch electrons and build the main bands file
            num_elec = get_number_of_electrons(scf_out_file)
            create_bands_input(scf_in_file, scf_out_file, num_elec, kpoints_text)
            
            # Create post-processing file
            create_bands_pp_input(scf_in_file, pp_file, material)
            
        except Exception as e:
            print(f"  -> Error processing {material}: {e}")