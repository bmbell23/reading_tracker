import os
import sys
import subprocess
from pathlib import Path
from typing import List
import unittest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class TestScriptExecution(unittest.TestCase):
    """Test suite for verifying script execution in the scripts directory."""

    @classmethod
    def setUpClass(cls):
        """Set up test class by finding all Python scripts."""
        cls.project_root = Path(__file__).parent.parent.parent
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
        console.print(f"\n[bold cyan]Running:[/bold cyan] {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test."""
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

    def run(self, result=None):
        """Override run to capture test results with rich formatting."""
        test_result = super().run(result)
        test_name = self._testMethodName

        if test_name in result.failures:
            console.print(f"[red]✗ {test_name} FAILED[/red]")
        elif test_name in result.errors:
            console.print(f"[red]✗ {test_name} ERROR[/red]")
        else:
            console.print(f"[green]✓ {test_name} PASSED[/green]")

        return test_result

    def run_script(self, script_path: Path, args: List[str] = None) -> subprocess.CompletedProcess:
        """Run a Python script with proper environment setup."""
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )

    def find_script_files(self) -> List[Path]:
        """Find all Python script files, excluding __init__.py and utils."""
        scripts = []
        for path in self.scripts_dir.rglob("*.py"):
            if path.name != "__init__.py" and "utils" not in str(path):
                scripts.append(path)
        return scripts

    def test_script_imports(self):
        """Test that verify_imports.py runs without errors."""
        script_path = self.scripts_dir / "verify_imports.py"
        result = self.run_script(script_path)
        self.assertEqual(result.returncode, 0,
            f"verify_imports.py failed with:\n{result.stderr}")

    def test_cleanup_scripts(self):
        """Test that cleanup scripts run without errors."""
        cleanup_dir = self.scripts_dir / "cleanup"
        scripts = [
            "cleanup_test_data.py",
            "cleanup_database.py",
            "cleanup_codebase.py"
        ]

        for script in scripts:
            script_path = cleanup_dir / script
            if script_path.exists():
                result = self.run_script(script_path)
                self.assertEqual(result.returncode, 0,
                    f"{script} failed with:\n{result.stderr}")

    def test_update_scripts(self):
        """Test that update scripts run without errors."""
        update_dir = self.scripts_dir / "updates"
        scripts = [
            "update_read_db.py",
            "update_version.py"
        ]

        for script in scripts:
            script_path = update_dir / script
            if script_path.exists():
                args = ["--check"] if script == "update_version.py" else None
                result = self.run_script(script_path, args)
                self.assertEqual(result.returncode, 0,
                    f"{script} failed with:\n{result.stderr}")

    def test_all_scripts_importable(self):
        """Test that all scripts can be imported without errors."""
        scripts = self.find_script_files()
        for script in scripts:
            rel_path = script.relative_to(self.project_root)
            module_path = str(rel_path).replace('/', '.').replace('\\', '.')[:-3]
            try:
                __import__(module_path)
            except ImportError as e:
                self.fail(f"Failed to import {rel_path}: {str(e)}")

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
