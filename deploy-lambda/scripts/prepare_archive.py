import json
import os
import shutil
import subprocess
import zipfile


def create_artifact():

    build_folder = "build"
    zipfile_name = os.path.join(build_folder, "lambda.zip")
    requirements_name = os.path.join(build_folder, "requirements.txt")

    # Start with clean environment
    if os.path.exists(build_folder):
        shutil.rmtree(build_folder)
    os.mkdir(build_folder)

    # Convert pipfile.lock to requirements.txt with pinned versions
    with open("Pipfile.lock") as pipfile:
        pipfile_json = json.load(pipfile)
        with open(requirements_name, "w") as requirements_file:
            requirements_file.write("\n".join(
                [package + detail.get("version", "") for package, detail in pipfile_json['default'].items()]
            ))

    # Install dependencies and copy in src
    if subprocess.call(["pip", "install", "--ignore-installed", f"--target={build_folder}",  "-r", requirements_name]) != 0:
        raise RuntimeError("Failed to install dependencies via pip")
    if subprocess.call(["cp", "-r", "src", build_folder]) != 0:
        raise RuntimeError("Failed to copy source code into build folder")

    # Build archive for upload
    if os.getenv("CREATE_ZIP"):
        with zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(build_folder):
                for file in files:
                    z.write(os.path.join(root, file),
                            os.path.relpath(os.path.join(root, file), os.path.join(build_folder, ".")))


if __name__ == "__main__":
    create_artifact()
