import importlib
import sys
from pathlib import Path
import unittest
from rich.console import Console
from rich.panel import Panel

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
            parts = line.split()
            if parts[1].startswith('reading_list.'):
                return 'reading_list'  # Return the package name for internal imports
            return parts[1].split('.')[0]
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
        all_failed_imports: dict[str, dict[Path, list[int]]] = {}

        for file in files:
            failed = self.verify_imports(file)
            if failed:
                for module, lines in failed.items():
                    if module not in all_failed_imports:
                        all_failed_imports[module] = {}
                    all_failed_imports[module][file] = lines

        # If there were any failed imports, fail the test with detailed information
        if all_failed_imports:
            # Build the detailed error message
            failure_msg = "\n[bold red]Import Verification Failed[/bold red]\n"

            for module, files_dict in all_failed_imports.items():
                failure_msg += f"\n[yellow]Module:[/yellow] {module}\n"
                for file_path, lines in files_dict.items():
                    rel_path = file_path.relative_to(self.project_root)
                    failure_msg += f"  [cyan]File:[/cyan] {rel_path}\n"
                    failure_msg += f"  [cyan]Lines:[/cyan] {', '.join(map(str, lines))}\n"

                # Add potential fix suggestions
                failure_msg += "\n[green]Potential fixes for[/green] [bold green]" + module + "[/bold green]:\n"
                if module.startswith('src.') or module.startswith('scripts.'):
                    failure_msg += "  • Create the missing module in your project structure\n"
                    failure_msg += "  • Check if the import path is correct\n"
                else:
                    failure_msg += f"  • Run: [bold]pip install {module}[/bold]\n"
                    failure_msg += f"  • Add [bold]{module}[/bold] to [italic]pyproject.toml[/italic] dependencies\n"

                failure_msg += "  • Verify the import statement spelling\n"
                failure_msg += "\n" + "─" * 50 + "\n"

            # Print the detailed formatted message
            console.print(Panel(
                failure_msg,
                title="Import Verification Results",
                border_style="red"
            ))

            # Create a concise summary for the test failure message
            summary = "\nMissing Dependencies Summary:\n"
            for module in all_failed_imports.keys():
                file_count = len(all_failed_imports[module])
                summary += f"• {module} (referenced in {file_count} file{'s' if file_count > 1 else ''})\n"

            self.fail(summary)

if __name__ == "__main__":
    unittest.main()
