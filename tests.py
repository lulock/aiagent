# tests.py

import unittest
from functions.get_files_info import run_python_file


class TestCalculator(unittest.TestCase):

    def test_run_python(self):
        print(run_python_file("calculator", "main.py"))
        print(run_python_file("calculator", "main.py", ["3 + 5"]))
        print(run_python_file("calculator", "tests.py"))
        print(run_python_file("calculator", "../main.py"))
        print(run_python_file("calculator", "nonexistent.py"))


if __name__ == "__main__":
    unittest.main()
