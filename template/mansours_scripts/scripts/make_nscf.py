import sys
import re
import math
import os

def get_number_of_electrons(outfile_path):
    """Parses the SCF output to find the number of electrons."""
    electrons = 0.0
    try:
        with open(outfile_path, 'r') as f:
            for line in f:
                if "number of electrons" in line:
                    # Line looks like: "     number of electrons       =     254.00"
                    try:
                        parts = line.split('=')
                        electrons = float(parts[1].strip().split()[0])
                        return electrons
                    except:
                        continue
    except FileNotFoundError:
        print(f"Warning: Output file {outfile_path} not found.")
    return 0.0

def create_nscf_input(infile_path, outfile_path, electrons):
    try:
        with open(infile_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file {infile_path} not found.")
        return

    # 1. Change calculation type
    # Handles calculation='scf', 'vc-relax', or 'relax'
    content = re.sub(r"calculation\s*=\s*['\"](scf|vc-relax|relax)['\"]", "calculation = 'nscf'", content)

    # 2. Calculate and Insert 'nbnd' (Number of Bands)
    # Formula: (Electrons / 2) + 20 buffer for empty states (DOS)
    if electrons > 0:
        nbnd = int(math.ceil(electrons / 2.0)) + 30 # Added slightly more for NSCF
        # Insert nbnd after 'nspin' or inside &SYSTEM
        if "nspin" in content:
             content = re.sub(r"(nspin\s*=\s*\d+)", f"\\1\n  nbnd = {nbnd}", content)
        else:
            # Fallback: insert at end of &SYSTEM
            content = re.sub(r"(/)", f"  nbnd = {nbnd}\n/", content, count=1)
        print(f"  -> Detected {electrons} electrons. Setting nbnd = {nbnd}")
    else:
        print("  -> Warning: Could not detect electron count. Keeping default nbnd.")

    # 3. Double the K_POINTS (Automatic Mesh)
    # NSCF requires a denser grid than SCF (usually 2x)
    # Matches: K_POINTS {automatic} 4 4 4 1 1 1
    
    def double_k(match):
        # match.group(1,2,3) are the grid numbers (e.g. 4 4 4)
        k1 = int(match.group(1)) * 2
        k2 = int(match.group(2)) * 2
        k3 = int(match.group(3)) * 2
        # match.group(4) is the remainder (offsets like 1 1 1)
        return f"K_POINTS {{automatic}}\n{k1} {k2} {k3}{match.group(4)}"

    # Regex to find K_POINTS block with 3 integers
    kpoint_pattern = r"K_POINTS\s*\{?automatic\}?[\s\n]*(\d+)\s+(\d+)\s+(\d+)(.*)"
    
    if re.search(kpoint_pattern, content, re.IGNORECASE):
        content = re.sub(kpoint_pattern, double_k, content, flags=re.IGNORECASE)
        print("  -> Doubled K-Points for NSCF accuracy.")
    else:
        print("  -> Warning: Could not find automatic K_POINTS to double.")

    # 4. Write the file
    # We want to replace 'scf' with 'nscf' in the filename
    # e.g. /path/to/scf.CoNiWO4.in -> /path/to/nscf.CoNiWO4.in
    
    dirname, basename = os.path.split(infile_path)
    new_basename = basename.replace("scf", "nscf").replace("relax", "nscf")
    
    # If filename didn't have 'scf' or 'relax', force prefix
    if new_basename == basename:
        new_basename = "nscf." + basename
        
    nscf_filename = os.path.join(dirname, new_basename)

    with open(nscf_filename, 'w') as f:
        f.write(content)
    
    print(f"  -> Success! Created {nscf_filename}")
    print("-" * 40)

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
        out_file = f"/trace/group/dabo/mansouro/unary/{material}/scf.{material}.out"
        in_file = f"/trace/group/dabo/mansouro/unary/{material}/scf.{material}.in"

        print(f"Processing {material}...")
        
        # 1. Get electrons from the output file
        num_elec = get_number_of_electrons(out_file)
        
        # 2. Create the NSCF input file
        create_nscf_input(in_file, out_file, num_elec)