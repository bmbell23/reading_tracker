"""
This functionality has been moved to tests/framework/test_imports.py
This file is kept temporarily for backward compatibility and will be removed in a future version.
"""
import sys
from pathlib import Path

def main():
    print("This script has been moved to tests/framework/test_imports.py")
    print("Please update your references to use the new location.")
    print("Running tests from new location...")

    # Import and run the new test
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tests.framework.test_imports import TestImports
    import unittest

    suite = unittest.TestLoader().loadTestsFromTestCase(TestImports)
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
