import os
files = []  #define output
scenario = "C:\\Users\\GHUIQ\\Downloads"
# Figure out which files or folders we are working with
#test OK
if os.path.isfile(scenario):
    files.append(scenario)
elif os.path.isdir(scenario):
    for f in os.listdir(scenario):
        scenario_file = os.path.join(scenario, f)

        if not os.path.isfile(scenario_file):
            continue

        if not scenario_file.lower().endswith(".csv"):
            continue

        files.append(scenario_file)
else:
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), scenario)

#output file
print(files)
