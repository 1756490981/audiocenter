"""Recover AudioHelper.exe from a packaged AudioCenter.exe.

This is how the C# source in AudioHelper/ was recovered in the first place,
and it stays as the tool of record for redoing that if the need ever arises:

    AudioCenter.exe (PyInstaller one-file bundle)
      -> AudioHelper.exe (.NET self-contained single-file bundle)
           -> AudioHelper.dll (97KB) -> ILSpy -> AudioHelper/

It is also the fallback used by the release workflow if AudioHelper/ ever
disappears from the repository again.

AudioCenter.exe is a PyInstaller one-file bundle; AudioHelper.exe sits inside
it as a plain data payload (added via `--add-data "AudioHelper.exe;."`), so no
bytecode decompilation is involved -- the file comes out byte-identical.

Usage:
    python tools/extract_audiohelper.py AudioCenter.exe [-o AudioHelper.exe]
"""
import argparse
import hashlib
import os
import sys

TARGET = 'audiohelper.exe'


def open_archive(bundle_path):
    """Open a PyInstaller one-file bundle for reading.

    Raises RuntimeError with a human-readable message on any failure.
    """
    if not os.path.exists(bundle_path):
        raise RuntimeError(f'{bundle_path} not found')
    try:
        from PyInstaller.archive.readers import CArchiveReader
    except ImportError:
        raise RuntimeError('PyInstaller is required (pip install pyinstaller)')
    try:
        return CArchiveReader(bundle_path)
    except Exception as exc:
        raise RuntimeError(
            f'could not read the PyInstaller archive in {bundle_path}: {exc}\n'
            '       Is this really a PyInstaller one-file build?'
        )


def extract_from_bundle(bundle_path):
    """Return the bytes of AudioHelper.exe stored inside `bundle_path`."""
    reader = open_archive(bundle_path)

    name = None
    for key in reader.toc:
        if os.path.basename(key).lower() == TARGET:
            name = key
            break

    if name is None:
        listing = '\n'.join(f'         {k}' for k in sorted(reader.toc)[:40])
        raise RuntimeError(
            f'no {TARGET} entry inside {bundle_path}\n'
            f'       Entries present:\n{listing}'
        )

    return reader.extract(name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('bundle', help='path to a packaged AudioCenter.exe')
    ap.add_argument('-o', '--output', default='AudioHelper.exe',
                    help='where to write the extracted helper (default: %(default)s)')
    args = ap.parse_args()

    try:
        data = extract_from_bundle(args.bundle)
    except RuntimeError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1

    with open(args.output, 'wb') as f:
        f.write(data)

    print(f'Extracted AudioHelper.exe from {args.bundle}')
    print(f'  -> {args.output}  ({len(data) / (1024 * 1024):.1f} MB)')
    print(f'  sha256: {hashlib.sha256(data).hexdigest()}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
