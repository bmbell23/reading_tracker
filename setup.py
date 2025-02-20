import subprocess
import sys
import venv
from pathlib import Path

def create_venv():
    # Create venv directory in project root
    venv_dir = Path("venv")
    if not venv_dir.exists():
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("Virtual environment already exists")

    # Get the path to the Python executable in the virtual environment
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        python_path = venv_dir / "bin" / "python"
        pip_path = venv_dir / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    # Install requirements
    print("Installing requirements...")
    requirements = [
        "sqlalchemy",
        "alembic",
        "pandas",
        "xlsxwriter",
    ]

    for req in requirements:
        print(f"Installing {req}...")
        subprocess.run([str(pip_path), "install", req])

    print("\nSetup complete! To activate the virtual environment:")
    if sys.platform == "win32":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")

if __name__ == "__main__":
    create_venv()