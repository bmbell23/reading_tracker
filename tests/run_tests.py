import unittest
import sys
from pathlib import Path
from termcolor import colored

def discover_and_run_tests():
    # Get the tests directory (where this script is located)
    tests_dir = Path(__file__).parent

    # Create a test loader
    loader = unittest.TestLoader()

    # Discover all tests in the tests directory and subdirectories
    # but exclude inventory tests
    test_suite = unittest.TestSuite()

    # Manually add test files, excluding inventory tests
    for test_file in tests_dir.rglob('test_*.py'):
        if 'test_inventory_operations.py' not in str(test_file):
            relative_path = test_file.relative_to(tests_dir.parent)
            module_name = str(relative_path).replace('\\', '.').replace('/', '.')[:-3]
            suite = loader.loadTestsFromName(module_name)
            test_suite.addTest(suite)

    # Create a test runner with verbosity=2 for detailed output
    runner = unittest.TextTestRunner(verbosity=2)

    print("\n" + "=" * 70)
    print(colored("Running Reading List Test Suite", "cyan", attrs=["bold"]))
    print("=" * 70 + "\n")

    # Run the tests and get the results
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 70)
    print(colored("Test Summary:", "cyan", attrs=["bold"]))
    print(f"Tests Run: {result.testsRun}")
    print(colored(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}", "green"))
    if result.failures:
        print(colored(f"Failures: {len(result.failures)}", "red"))
    if result.errors:
        print(colored(f"Errors: {len(result.errors)}", "red"))
    print("=" * 70 + "\n")

    # Return 0 if all tests passed, 1 if any failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(discover_and_run_tests())
