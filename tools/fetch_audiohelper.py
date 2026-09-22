"""Obtain AudioHelper.exe for packaging, without rebuilding it.

Normally the release workflow does not need this: AudioHelper/ holds the C#
source and is built with `dotnet publish`. This script is the fallback for if
that source ever goes missing again, resolving a prebuilt AudioHelper.exe by,
in order of preference:

  1. downloading it from an explicit URL  (--url, or the AUDIOHELPER_URL
     repository variable on CI)
  2. recovering it from the AudioCenter.exe attached to an existing release
     (--bundle-tag), which is what the old README told every user to do by
     hand

Usage:
    python tools/fetch_audiohelper.py --repo owner/name [--url URL] [-o out]
"""
import argparse
import hashlib
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_audiohelper import extract_from_bundle  # noqa: E402

DEFAULT_BUNDLE_TAG = 'audio'
BUNDLE_ASSET = 'AudioCenter.exe'


def download(url, dest):
    """Stream `url` to `dest`. Raises RuntimeError with a readable message."""
    print(f'Downloading {url}')
    try:
        with urllib.request.urlopen(url, timeout=120) as resp, open(dest, 'wb') as f:
            total = 0
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'HTTP {exc.code} fetching {url}')
    except urllib.error.URLError as exc:
        raise RuntimeError(f'network error fetching {url}: {exc.reason}')
    print(f'  -> {dest}  ({total / (1024 * 1024):.1f} MB)')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('-o', '--output', default='AudioHelper.exe',
                    help='where to write the helper (default: %(default)s)')
    ap.add_argument('--url', default=os.environ.get('AUDIOHELPER_URL', ''),
                    help='direct download URL for AudioHelper.exe')
    ap.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY', ''),
                    help='owner/name used to locate an existing release')
    ap.add_argument('--bundle-tag', default=DEFAULT_BUNDLE_TAG,
                    help='release tag holding %s (default: %%(default)s)' % BUNDLE_ASSET)
    ap.add_argument('--keep-bundle', action='store_true',
                    help='keep the downloaded %s for inspection' % BUNDLE_ASSET)
    args = ap.parse_args()

    if args.url:
        try:
            download(args.url, args.output)
        except RuntimeError as exc:
            print(f'ERROR: {exc}', file=sys.stderr)
            return 1
    else:
        if not args.repo:
            print('ERROR: neither --url nor --repo was provided, so there is no\n'
                  '       way to locate a prebuilt AudioHelper.exe.', file=sys.stderr)
            return 1

        bundle_url = (f'https://github.com/{args.repo}/releases/download/'
                      f'{args.bundle_tag}/{BUNDLE_ASSET}')
        bundle_path = BUNDLE_ASSET
        try:
            download(bundle_url, bundle_path)
            print(f'Recovering AudioHelper.exe from {BUNDLE_ASSET} ...')
            data = extract_from_bundle(bundle_path)
        except RuntimeError as exc:
            print(f'ERROR: {exc}', file=sys.stderr)
            print('\nTo fix this, either:\n'
                  '  * set the repository variable AUDIOHELPER_URL to a direct link\n'
                  '    to a standalone AudioHelper.exe, or\n'
                  '  * upload a standalone AudioHelper.exe to a release, or\n'
                  '  * commit the AudioHelper C# source so it can be built.',
                  file=sys.stderr)
            return 1
        finally:
            if not args.keep_bundle and os.path.exists(bundle_path):
                os.remove(bundle_path)

        with open(args.output, 'wb') as f:
            f.write(data)

    size = os.path.getsize(args.output)
    with open(args.output, 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f'Ready: {args.output}  ({size / (1024 * 1024):.1f} MB)')
    print(f'  sha256: {digest}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
