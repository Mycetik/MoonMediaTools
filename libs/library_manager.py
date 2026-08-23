import sys
import os
import subprocess
import importlib.metadata
from logger.logger import log
from util.network import is_internet_available

def get_package_version(package_name):
    base_name = package_name.split('[')[0]
    try:
        return importlib.metadata.version(base_name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"

def is_package_installed(package_name):
    base_name = package_name.split('[')[0]
    try:
        importlib.metadata.version(base_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False

def install_libraries(config_path="libs.txt"):
    if not is_internet_available():
        log.warn(f"No internet connection, skipping installation libs.")
        return
    if not os.path.exists(config_path):
        log.warn(f"Config file '{config_path}' not found. Skipping dependency check.")
        return

    pypi_aliases = {
        "yaml": "PyYAML"
    }

    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "::" not in line:
                continue

            pkg_name, pkg_type = [part.strip() for part in line.split("::")]

            pypi_name = pypi_aliases.get(pkg_name.lower(), pkg_name)

            if pkg_type == "static":
                if not is_package_installed(pypi_name):
                    log.info(f"Installing dependency: {pypi_name}...")
                    _run_pip(["install", pypi_name])
            elif pkg_type == "dynamic":
                log.info(f"Updating: {pypi_name}...")
                _run_pip(["install", "--upgrade", pypi_name])

                current_version = get_package_version(pypi_name)
                log.info(f"{pypi_name} {current_version}")
            else:
                log.warn(f"Unknown type '{pkg_type}' for package '{pkg_name}'. Use 'static' or 'dynamic'.")


def _run_pip(args):
    command = [sys.executable, "-m", "pip"] + args + ["--disable-pip-version-check", "--quiet"]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"Pip command failed for args {args}: {result.stderr.strip()}")
            raise RuntimeError(f"Failed to install package. Check logs for details.")
    except Exception as e:
        raise RuntimeError(f"Pip execution error: {e}")