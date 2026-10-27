"""Единая команда запуска всех тестов: python run_tests.py"""
import glob
import shutil
import subprocess
import sys

code = subprocess.call([sys.executable, "-m", "pytest", "-q"])
if shutil.which("node"):
    code |= subprocess.call(["node", "--test", *glob.glob("tests/frontend/*.test.js")])
else:
    print("node не найден: тесты фронтенда пропущены (установите Node.js 18+)")
sys.exit(code)
