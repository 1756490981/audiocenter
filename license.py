"""License verification — one license per machine."""
import hashlib
import hmac
import json
import base64
import os
import subprocess
import sys

# Secret key (shared with activate.py)
_SECRET = 'Ay' + 'un' + 'Aud' + 'io' + '#20' + '26!' + 'Li' + 'ce' + 'ns' + 'e'

CONTACT = '微信：AyunAudio'
_APP_NAME = 'AudioCenter'


def _run_ps(ps_cmd: str) -> str:
    """Run a PowerShell command and return trimmed output."""
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_cmd],
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        val = r.stdout.strip()
        if val and val != '' and 'Default string' not in val:
            return val
    except Exception:
        pass
    return ''


def get_machine_id() -> str:
    """Generate a 16-char hex machine fingerprint from hardware IDs."""
    parts = []
    for ps in [
        'Get-CimInstance Win32_Processor | Select-Object -ExpandProperty ProcessorId',
        'Get-CimInstance Win32_BaseBoard | Select-Object -ExpandProperty SerialNumber',
        'Get-CimInstance Win32_DiskDrive | Select-Object -ExpandProperty SerialNumber',
    ]:
        val = _run_ps(ps)
        parts.append(val if val else 'unknown')

    raw = '|'.join(parts)
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return digest[:16].upper()


def generate_license(machine_id: str) -> str:
    """Generate a license string for a given machine ID. (Used by activate.py)"""
    payload = {'machine': machine_id, 'expire': 0}
    msg = f"{payload['machine']}|{payload['expire']}"
    sig = hmac.new(_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    payload['sig'] = sig
    return base64.b64encode(json.dumps(payload).encode()).decode()


def verify_license(license_file: str = 'license.dat') -> tuple:
    """Verify license file. Returns (ok: bool, machine_id: str, error: str)."""
    machine_id = get_machine_id()

    # Resolve license file path (next to exe or script)
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, license_file)

    if not os.path.exists(path):
        return False, machine_id, '授权文件不存在'

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read().strip()
        payload = json.loads(base64.b64decode(data))
    except Exception:
        return False, machine_id, '授权文件格式错误'

    # Verify signature
    msg = f"{payload.get('machine', '')}|{payload.get('expire', 0)}"
    expected_sig = hmac.new(_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(payload.get('sig', ''), expected_sig):
        return False, machine_id, '授权签名无效'

    # Verify machine ID
    if payload.get('machine', '').upper() != machine_id:
        return False, machine_id, '授权码与本机不匹配'

    # Check expiry (0 = permanent)
    expire = payload.get('expire', 0)
    if expire != 0:
        import time
        if time.time() > expire:
            return False, machine_id, '授权已过期'

    return True, machine_id, ''
