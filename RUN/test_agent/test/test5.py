import subprocess
import os

# Change directory
project_path = r"F:\TA\project"
os.chdir(project_path)

# Build Docker image without cache

#build_command = ["docker", "build", "--no-cache", "-t", "z1", "."]
#print("Running:", " ".join(build_command))
#subprocess.run(build_command, check=True)

# Run Docker container with GPU and volume mount
run_command = [
    "docker", "run","--gpus", "all",
    "-v", "F:/TA/dataset:/app/dataset",
    "z1"
]
print("Running:", " ".join(run_command))
subprocess.run(run_command)
