import importlib
import sys
from pathlib import Path
import unittest
from rich.console import Console

console = Console()

class TestImports(unittest.TestCase):
    """Test suite for verifying project imports."""

    @classmethod
    def setUpClass(cls):
        """Set up test class by finding project root."""
        cls.project_root = Path(__file__).parent.parent.parent
        if str(cls.project_root) not in sys.path:
            sys.path.insert(0, str(cls.project_root))

    def setUp(self):
        """Set up before each test."""
        console.print(f"\n[bold cyan]Running:[/bold cyan] {self._testMethodName}")

    def find_python_files(self) -> list[Path]:
        """Find all Python files in the project."""
        return [p for p in self.project_root.glob("**/*.py")
                if "venv" not in str(p) and ".git" not in str(p)]

    def parse_import_line(self, line: str) -> str:
        """Extract the base module name from an import line."""
        line = line.strip()
        if line.startswith('from '):
            return line.split()[1].split('.')[0]
        elif line.startswith('import '):
            return line.split()[1].split('.')[0]
        return ''

    def verify_imports(self, file_path: Path) -> dict[str, list[int]]:
        """Verify imports in a Python file."""
        failed_imports: dict[str, list[int]] = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not (line.startswith('import ') or line.startswith('from ')):
                        continue

                    module = self.parse_import_line(line)
                    if not module or module in ('src', 'scripts'):
                        continue

                    try:
                        importlib.import_module(module)
                    except ImportError:
                        if module not in failed_imports:
                            failed_imports[module] = []
                        failed_imports[module].append(line_num)
        except Exception as e:
            self.fail(f"Error processing {file_path}: {e}")

        return failed_imports

    def test_all_project_imports(self):
        """Test that all imports in the project are valid."""
        files = self.find_python_files()
        all_failed_imports: dict[str, set[Path]] = {}

        for file in files:
            failed = self.verify_imports(file)
            if failed:
                rel_path = file.relative_to(self.project_root)
                for module, lines in failed.items():
                    if module not in all_failed_imports:
                        all_failed_imports[module] = set()
                    all_failed_imports[module].add(file)
                    console.print(f"[red]Failed imports in {rel_path}:[/red]")
                    console.print(f"  - {module} (lines: {', '.join(map(str, lines))})")

        # If there were any failed imports, fail the test
        if all_failed_imports:
            failure_msg = "\nSummary of missing dependencies:\n"
            for module, files in all_failed_imports.items():
                file_count = len(files)
                failure_msg += f"  - {module} (used in {file_count} file{'s' if file_count > 1 else ''})\n"
            self.fail(failure_msg)

if __name__ == "__main__":
    unittest.main()