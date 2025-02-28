import subprocess
import sys
import venv
from pathlib import Path
from setuptools import setup

# Project version
VERSION = "2.2.7"

def create_venv():
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("Virtual environment already exists")

    python_path = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
    pip_path = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / ("pip.exe" if sys.platform == "win32" else "pip")

    print("Upgrading pip...")
    subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    print("Installing project in development mode...")
    subprocess.run([str(pip_path), "install", "-e", "."])

    print("\nSetup complete! To activate the virtual environment:")
    activate_cmd = r"venv\Scripts\activate" if sys.platform == "win32" else "source venv/bin/activate"
    print(f"    {activate_cmd}")

if __name__ == "__main__":
    setup(
        name="reading_list",
        version=VERSION,
        description="Reading List Tracker",
        author="Your Name",
        author_email="your.email@example.com",
        packages=["reading_list"],
        package_dir={"": "src"},
        python_requires=">=3.8",
    )
    create_venv()
