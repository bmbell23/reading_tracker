import subprocess
import sys
import venv
from pathlib import Path
from setuptools import setup, find_packages, find_namespace_packages

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
    # Find packages in both structures
    packages = []
    
    # Find packages in root directory (old structure)
    root_packages = find_packages(include=['scripts*', 'tests*', 'src*'])
    packages.extend(root_packages)
    
    # Find packages in src directory (new structure)
    src_packages = find_namespace_packages(where="src", include=["reading_list*"])
    packages.extend(src_packages)
    
    # Remove duplicates while preserving order
    packages = list(dict.fromkeys(packages))

    setup(
        name="reading_list",
        version="2.2.6",
        packages=packages,
        package_dir={
            "": ".",                          # For root-level packages
            "reading_list": "src/reading_list" # For new structure
        },
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
            "plotly>=5.3.0",
            "dash>=2.0.0",
        ],
        python_requires='>=3.8',
        entry_points={
            'console_scripts': [
                'reading-db-transfer=reading_list.cli.db_transfer_cli:main',
                'reading-update=reading_list.cli.update_entries:main',
                'reading-excel-template=reading_list.cli.excel_template_cli:main',
            ],
        },
    )
    create_venv()
