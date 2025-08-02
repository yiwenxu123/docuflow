import pytest
import os

if __name__ == "__main__":
    test_file = os.path.abspath("tests/test_all_conversions.py")
    if not os.path.exists(test_file):
        print(f"Error: Test file not found at {test_file}")
    else:
        pytest.main(['-v', test_file])