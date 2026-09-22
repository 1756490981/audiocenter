"""Import every module in the project and report the first failure.

Guards against the failure mode where `requirements.txt` drifts out of sync
with what the code actually imports: a clean clone installs fine, then dies on
`import pystray` the moment `main.py` runs. Running this in CI turns that into
a build failure with the package name in the message.

Usage:
    python tools/check_imports.py
"""
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Import target -> the real module whose absence it signals. PyInstaller-style
# behaviour: import failures for submodules of a top-level dist are reported
# against the top-level distribution so the fix is obvious.
MODULES = [
    'themecolors',
    'iconutil',
    'audio',
    'tabs.mixer',
    'tabs.playback',
    'tabs.recording',
    'tabs.profiles',
    'tabs.studio',
    'main',
]

# top-level import name -> pip install name, where they differ
PACKAGE_ALIASES = {
    'PIL': 'Pillow',
    'pycaw': 'pycaw',
    'customtkinter': 'customtkinter',
    'pystray': 'pystray',
}


def main():
    failures = []

    for name in MODULES:
        try:
            __import__(name)
        except ModuleNotFoundError as exc:
            missing = (exc.name or '').split('.')[0]
            package = PACKAGE_ALIASES.get(missing, missing)
            failures.append(
                f'  {name:20s} -> missing module {missing!r} '
                f'(add {package!r} to requirements.txt)'
            )
        except Exception as exc:
            failures.append(
                f'  {name:20s} -> {type(exc).__name__}: {exc}\n'
                + ''.join(traceback.format_exc(limit=3))
            )

    if failures:
        print('Import check FAILED:\n')
        print('\n'.join(failures))
        return 1

    print(f'Import check OK ({len(MODULES)} modules)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
