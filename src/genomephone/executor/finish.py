import subprocess
import shutil

from pathlib import Path


def finish_project(project) -> str:
    # initialize chunk folder
    proj_folder = Path(f"{project.id}")
    proj_folder.mkdir(exist_ok=False)

    # initialize chunk vcfs
    vcfs = []
    for target in project.targets:
        vcf_file = proj_folder / f"{target.name}.vcf"
        with vcf_file.open("w") as f:
            f.write(target.chunk.result)
        vcfs.append(vcf_file)

    # initialize output file
    output_file = proj_folder / "output.vcf"
    
    # merge vcf
    command = ["bcftools", "merge"] + [str(v) for v in vcfs] + [ "-o", str(output_file)]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(f"Error merging VCF files: {result.stderr.decode('utf-8')}")
    else:
        print(f"Merged VCF files into {output_file}")
    
    with output_file.open("r") as f:
        result = f.read()
    
    shutil.rmtree(proj_folder)

    return result