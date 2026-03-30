import re
import os

BASE_DIR = "/trace/group/dabo/mansouro/unary"

MATERIALS = [
    "CoWO4",
    "CuWO4",
    "FeWO4",
    "MnWO4",
    "NiWO4",
    "ZnWO4",
]


def extract_param(content, key):
    """Extracts a namelist parameter value (string or numeric) from QE input content."""
    # First try: quoted string (handles paths like './tmp/' that contain slashes)
    match = re.search(rf"{key}\s*=\s*['\"]([^'\"]+)['\"]", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: unquoted value (no slashes, spaces, or commas)
    match = re.search(rf"{key}\s*=\s*([^\s,/]+)", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def get_fermi_energy(outfile_path):
    """
    Parses a pw.x output file (nscf or scf) to find the Fermi energy.
    Returns the Fermi energy as a float, or None if not found.
    """
    fermi = None
    try:
        with open(outfile_path, "r") as f:
            for line in f:
                # Line looks like:    the Fermi energy is    X.XXXX ev
                if "the Fermi energy is" in line:
                    try:
                        fermi = float(line.split("is")[1].strip().split()[0])
                    except (IndexError, ValueError):
                        continue
    except FileNotFoundError:
        print(f"  -> Warning: Output file {outfile_path} not found.")
    return fermi


def create_projwfc_input(nscf_infile_path, nscf_outfile_path, output_dir, material):
    """
    Reads the nscf input file to extract prefix and outdir, optionally reads
    the Fermi energy from the nscf output, and writes a projwfc namelist file.
    """
    # --- Read nscf input to extract parameters ---
    try:
        with open(nscf_infile_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  -> Error: Input file {nscf_infile_path} not found. Skipping.")
        return

    prefix = extract_param(content, "prefix") or material
    outdir = extract_param(content, "outdir") or "./tmp/"

    print(f"  -> Extracted prefix  = '{prefix}'")
    print(f"  -> Extracted outdir  = '{outdir}'")

    # --- Optionally get Fermi energy from nscf output ---
    fermi = get_fermi_energy(nscf_outfile_path)
    if fermi is not None:
        emin = round(fermi - 20.0, 4)
        emax = round(fermi + 20.0, 4)
        print(f"  -> Fermi energy = {fermi} eV  =>  Emin = {emin}, Emax = {emax}")
    else:
        # Sensible defaults relative to zero (no Fermi found)
        emin = -20.0
        emax =  20.0
        print(f"  -> Warning: Fermi energy not found. Using default Emin={emin}, Emax={emax}.")

    # --- Build the &PROJWFC namelist ---
    projwfc_content = f"""&PROJWFC
  prefix  = '{prefix}'
  outdir  = '{outdir}'
  filpdos = '{prefix}'
  Emin    = {emin}
  Emax    = {emax}
  DeltaE  =  0.01
/
"""

    # --- Write the file ---
    projwfc_filename = os.path.join(output_dir, f"projwfc.{material}.in")
    with open(projwfc_filename, "w") as f:
        f.write(projwfc_content)

    print(f"  -> Success! Created {projwfc_filename}")
    print("-" * 40)


if __name__ == "__main__":
    for material in MATERIALS:
        print(f"\n--- Processing {material} ---")

        nscf_in  = f"{BASE_DIR}/{material}/nscf.{material}.in"
        nscf_out = f"{BASE_DIR}/{material}/nscf.{material}.out"
        mat_dir  = f"{BASE_DIR}/{material}"

        if not os.path.exists(nscf_in):
            print(f"  -> Skipping: Cannot find {nscf_in}")
            print("-" * 40)
            continue

        create_projwfc_input(nscf_in, nscf_out, mat_dir, material)
