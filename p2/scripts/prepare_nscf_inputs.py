import os

# folder to process
folders = ["nscf_inputs_FM", "nscf_inputs_AFM"]
nbnd_value = 80
kpoints_new = "12 12 12 1 1 1"

for folder in folders:
    for fname in os.listdir(folder):
        if fname.endswith(".in"):
            path = os.path.join(folder, fname)
            with open(path, "r") as f:
                lines = f.readlines()

            new_lines = []
            in_system = False
            in_kpoints = False
            kpoints_replaced = False
            nbnd_added = False

            for line in lines:
                # Change calculation type
                if "&CONTROL" in line:
                    in_control = True
                if "calculation" in line and "scf" in line:
                    line = "calculation = 'nscf'\n"

                # Add nbnd in &SYSTEM
                if "&SYSTEM" in line:
                    in_system = True
                if in_system and line.strip() == "/":
                    if not nbnd_added:
                        new_lines.append(f"nbnd = {nbnd_value}\n")
                        nbnd_added = True
                    in_system = False

                # Replace K_POINTS
                if line.strip().startswith("K_POINTS"):
                    in_kpoints = True
                    new_lines.append(line)
                    continue
                if in_kpoints:
                    new_lines.append(kpoints_new + "\n")
                    in_kpoints = False
                    kpoints_replaced = True
                    continue

                new_lines.append(line)

            with open(path, "w") as f:
                f.writelines(new_lines)

print("NSCF input files updated.")
