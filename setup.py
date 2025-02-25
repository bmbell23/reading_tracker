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
        version="1.9.2",
        packages=find_packages(include=['src*', 'scripts*', 'tests*']),
        package_data={
            'templates': ['excel/*', 'email/*'],
            'config': ['*.yaml'],
            'docs': ['*.md', 'images/*'],
        },
        install_requires=[
            "flask>=2.0.0",
            "flask-wtf>=1.0.0",
            "sqlalchemy>=1.4.0",
            "alembic>=1.7.0",
            "pandas>=1.3.0",
            "xlsxwriter>=3.0.0",
            "openpyxl>=3.0.0",
            "tabulate>=0.9.0",
            "termcolor>=2.0.0",
            "rich>=10.0.0",
            "python-dotenv>=0.19.0",
        ],
        python_requires='>=3.8',
    )
    create_venv()
