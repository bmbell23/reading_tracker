import os
import sys
import subprocess
from pathlib import Path
from typing import List
import unittest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import importlib.util

console = Console()

class TestScriptExecution(unittest.TestCase):
    """Test suite for verifying script execution in the scripts directory."""

    @classmethod
    def setUpClass(cls):
        """Set up test class by finding all Python scripts."""
        cls.project_root = Path(__file__).parents[2]
        cls.scripts_dir = cls.project_root / "scripts"

        # Add project root to Python path
        if str(cls.project_root) not in sys.path:
            sys.path.insert(0, str(cls.project_root))

        # Create test database
        cls.test_db_path = cls.project_root / "test_reading_list.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{cls.test_db_path}"

    @classmethod
    def tearDownClass(cls):
        """Clean up test artifacts."""
        if cls.test_db_path.exists():
            cls.test_db_path.unlink()

    def setUp(self):
        """Set up test environment before each test."""
        os.environ["TESTING"] = "true"

    def tearDown(self):
        """Clean up after each test."""
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

    def run(self, result=None):
        """Override run to capture test results."""
        test_result = super().run(result)
        test_name = self._testMethodName

        # Only print failures and errors
        if test_name in result.failures:
            console.print(f"[red]✗ {test_name} FAILED[/red]")
        elif test_name in result.errors:
            console.print(f"[red]✗ {test_name} ERROR[/red]")

        return test_result

    def run_script(self, script_path: Path, args: List[str] = None) -> subprocess.CompletedProcess:
        """Run a Python script with proper environment setup."""
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )

        if result.returncode != 0:
            console.print(f"\n[bold red]Script Execution Failed:[/bold red] {script_path.name}")
            console.print("\n[yellow]Command:[/yellow]")
            console.print(f"  {' '.join(cmd)}")

            if result.stdout:
                console.print("\n[yellow]Standard Output:[/yellow]")
                console.print(Panel(result.stdout.strip(), border_style="yellow"))

            if result.stderr:
                console.print("\n[red]Error Output:[/red]")
                console.print(Panel(result.stderr.strip(), border_style="red"))

            console.print("\n[yellow]Environment:[/yellow]")
            console.print(f"  PYTHONPATH: {env['PYTHONPATH']}")
            console.print(f"  Working Directory: {os.getcwd()}")

        return result

    def find_script_files(self) -> List[Path]:
        """Find all Python script files, excluding __init__.py and utils."""
        scripts = []
        for path in self.scripts_dir.rglob("*.py"):
            if path.name != "__init__.py" and "utils" not in str(path):
                scripts.append(path)
        return scripts

    def test_cleanup_scripts(self):
        """Test cleanup scripts exist"""
        cleanup_dir = self.project_root / 'scripts' / 'cleanup'
        self.assertTrue(cleanup_dir.exists(), "Cleanup directory not found")
        
        scripts = list(cleanup_dir.glob('*.py'))
        self.assertGreater(len(scripts), 0, "No cleanup scripts found")

    def test_update_scripts(self):
        """Test update scripts exist"""
        update_dir = self.project_root / 'scripts' / 'updates'
        self.assertTrue(update_dir.exists(), "Updates directory not found")
        
        scripts = list(update_dir.glob('*.py'))
        self.assertGreater(len(scripts), 0, "No update scripts found")

    def test_all_scripts_importable(self):
        """Test that all Python scripts can be imported"""
        script_dir = self.project_root / 'scripts'
        failed_imports = []
        
        for script_path in script_dir.rglob('*.py'):
            if script_path.name.startswith('__'):
                continue
                
            try:
                spec = importlib.util.spec_from_file_location(
                    script_path.stem, 
                    script_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                failed_imports.append(f"{script_path.relative_to(self.project_root)}: {str(e)}")
        
        if failed_imports:
            self.fail(f"Failed imports:\n" + "\n".join(failed_imports))

def print_test_summary(result):
    """Print a formatted summary of test results."""
    table = Table(title="Script Test Results", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="white")

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    table.add_row("Total Tests", str(total))
    table.add_row("Passed", f"[green]{passed}[/green]")
    if failed:
        table.add_row("Failed", f"[red]{failed}[/red]")
    if errors:
        table.add_row("Errors", f"[red]{errors}[/red]")

    console.print("\n")
    console.print(table)
    console.print("\n")

if __name__ == "__main__":
    console.print("\n[bold cyan]Running Script Tests[/bold cyan]\n")
    console.print("=" * 50)

    # Create a test suite and runner
    suite = unittest.TestLoader().loadTestsFromTestCase(TestScriptExecution)
    result = unittest.TestResult()
    suite.run(result)

    # Print summary
    print_test_summary(result)

    # Exit with appropriate status code
    sys.exit(len(result.failures) + len(result.errors))
