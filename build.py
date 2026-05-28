"""AudioCenter onefile build script — run with: python build.py"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory: {os.getcwd()}")

# Check AudioHelper.exe
if not os.path.exists("AudioHelper.exe"):
    print("ERROR: AudioHelper.exe not found!")
    sys.exit(1)

# Clean
import shutil
for d in ["build", "dist"]:
    if os.path.exists(d):
        shutil.rmtree(d)
for f in ["AudioCenter.spec"]:
    if os.path.exists(f):
        os.remove(f)

print("\nStarting PyInstaller --onefile... (2-3 minutes)\n")

result = subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--onefile", "--windowed",
    "--name", "AudioCenter_Portable",
    "--add-data", "AudioHelper.exe;.",
    "--hidden-import", "PIL._tkinter_finder",
    "--exclude-module", "numpy",
    "--exclude-module", "numpy._core",
    "--exclude-module", "numpy.libs",
    "--exclude-module", "numpy.random",
    "--exclude-module", "numpy.fft",
    "--exclude-module", "numpy.linalg",
    "--exclude-module", "numpy.polynomial",
    "main.py",
])

if result.returncode != 0:
    print("\nBUILD FAILED")
    sys.exit(1)

exe = "dist/AudioCenter_Portable.exe"
size_mb = os.path.getsize(exe) / (1024 * 1024)
print(f"\n=== Build complete ===")
print(f"  {exe}  ({size_mb:.1f} MB)")
