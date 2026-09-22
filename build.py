"""AudioCenter onefile build script — run with: python build.py

This is the canonical build entry point. build.bat is a thin wrapper around it
so that the PyInstaller flags live in exactly one place; the two scripts had
drifted apart (different output names, and build.py silently dropped icon.ico
and most of the hidden imports).
"""
import os
import shutil
import subprocess
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_NAME = "AudioCenter"

# These are imported lazily or by module name, so PyInstaller's static analysis
# alone does not always find them.
HIDDEN_IMPORTS = [
    "PIL._tkinter_finder",
    "themecolors",
    "iconutil",
    "audio",
    "tabs.mixer",
    "tabs.playback",
    "tabs.recording",
    "tabs.profiles",
    "tabs.studio",
]

# numpy arrives as a transitive dependency but is never used here; dropping it
# keeps the bundle roughly 30MB smaller.
EXCLUDED_MODULES = [
    "numpy",
    "numpy._core",
    "numpy.libs",
    "numpy.random",
    "numpy.fft",
    "numpy.linalg",
    "numpy.polynomial",
]

REQUIRED_FILES = ["AudioHelper.exe", "icon.ico"]


def fail(msg):
    print(f"\nERROR: {msg}")
    sys.exit(1)


def main():
    print(f"Working directory: {os.getcwd()}")

    for name in REQUIRED_FILES:
        if not os.path.exists(name):
            fail(
                f"{name} not found.\n"
                "  AudioHelper.exe is the C# backend, built from AudioHelper/:\n"
                "    dotnet publish AudioHelper/AudioHelper.csproj -c Release \\\n"
                "      --self-contained true -r win-x64 -p:PublishSingleFile=true -o out\n"
                "    cp out/AudioHelper.exe .\n"
                "  (CI does this for you -- see .github/workflows/release.yml)"
            )

    # Clean first, so the result never depends on leftovers from a previous run.
    for d in ("build", "dist"):
        shutil.rmtree(d, ignore_errors=True)
    spec = f"{OUTPUT_NAME}.spec"
    if os.path.exists(spec):
        os.remove(spec)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--noconfirm", "--clean",
        "--name", OUTPUT_NAME,
        "--icon", "icon.ico",
        # Ask Windows to elevate on launch. The app needs administrator rights
        # for device enable/disable and device format changes, and the README
        # already told users to expect a UAC prompt.
        "--uac-admin",
        # AudioHelper.exe is spawned at runtime and icon.ico is loaded for the
        # window and tray icon -- both must be inside the bundle.
        "--add-data", "AudioHelper.exe;.",
        "--add-data", "icon.ico;.",
    ]
    for module in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", module]
    for module in EXCLUDED_MODULES:
        cmd += ["--exclude-module", module]
    cmd.append("main.py")

    print("\nBuilding with PyInstaller --onefile (this takes a few minutes)...\n")
    if subprocess.run(cmd).returncode != 0:
        fail("PyInstaller failed.")

    exe = os.path.join("dist", f"{OUTPUT_NAME}.exe")
    if not os.path.exists(exe):
        fail(f"{exe} was not produced.")

    size_mb = os.path.getsize(exe) / (1024 * 1024)
    print("\n=== Build complete ===")
    print(f"  {exe}  ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
