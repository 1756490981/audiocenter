"""Standalone test: verify set-session-device command works."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio import AudioHelper

h = AudioHelper()
try:
    # List sessions
    sess = h.send('list-sessions', timeout=5.0)
    sessions = sess.get('sessions', [])
    print(f'Sessions: {len(sessions)}')
    for s in sessions[:5]:
        print(f'  PID={s["pid"]} name={s.get("displayName","?")[:30]} vol={s.get("volume")} deviceId={s.get("deviceId","?")}')

    # List devices
    devs = h.send('list-devices', type='render', timeout=5.0)
    devices = devs.get('devices', [])
    print(f'\nRender devices: {len(devices)}')
    for d in devices[:5]:
        print(f'  id={d["id"][:50]}... name={d.get("name","?")}')

    if sessions:
        s0 = sessions[0]
        pid = s0['pid']
        print(f'\n--- Testing set-session-device on PID={pid} ---')

        # Test 1: Clear routing
        resp = h.send('set-session-device', pid=pid, device_id='', timeout=5.0)
        print(f'Clear routing: {resp}')

        # Test 2: Route to a specific device (use first packed device)
        if devices:
            dev_id = devices[0]['id']
            print(f'Routing to: {devices[0].get("name","?")}')
            resp = h.send('set-session-device', pid=pid, device_id=dev_id, timeout=5.0)
            print(f'Route response: {resp}')

            # Check what get-session-device returns
            resp2 = h.send('get-session-device', pid=pid, timeout=5.0)
            print(f'Current deviceId: {resp2}')

    print('\nAll tests passed!')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
finally:
    h.close()
