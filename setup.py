import subprocess
import sys
import venv
from pathlib import Path
from setuptools import setup, find_packages

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

    # Install the project in development mode
    print("Installing project in development mode...")
    subprocess.run([str(pip_path), "install", "-e", "."])

    print("\nSetup complete! To activate the virtual environment:")
    if sys.platform == "win32":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")

if __name__ == "__main__":
    setup(
        name="reading_list",
        version="1.6.9",
        packages=find_packages(include=['src', 'src.*', 'tests', 'tests.*', 'scripts', 'scripts.*']),
        package_dir={'': '.'},
        package_data={
            'templates': ['excel/*', 'email/*'],
            'config': ['.env.example', 'logging.yaml'],
            'docs': ['*.md', 'images/*'],
            'data': ['db/.gitkeep', 'csv/.gitkeep', 'backups/.gitkeep'],
        },
        install_requires=[
            "sqlalchemy",
            "alembic",
            "pandas",
            "xlsxwriter",
            "openpyxl",
            "tabulate>=0.9.0",
            "termcolor",
            "rich",
            "python-dotenv"
        ],
        python_requires='>=3.8',
    )
    create_venv()
