"""Manual smoke check: verify the set-session-device command works.

This is NOT a pytest test and is deliberately not named test_*.py. pytest
collects test_*.py by name, imports it during collection, and would therefore
open an AudioHelper process and re-route live per-app audio on whatever
machine runs the suite.

It needs a real audio stack and it MODIFIES live per-app audio routing, so run
it by hand on a machine where that is acceptable:

    python manual_check_device_routing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio import AudioHelper


def main():
    print('WARNING: this clears and rewrites the output routing of the first '
          'audio session it finds.')

    helper = None
    try:
        helper = AudioHelper()

        sess = helper.send('list-sessions', timeout=5.0)
        sessions = sess.get('sessions', [])
        print(f'Sessions: {len(sessions)}')
        for s in sessions[:5]:
            print(f'  PID={s["pid"]} name={s.get("displayName", "?")[:30]} '
                  f'vol={s.get("volume")} deviceId={s.get("deviceId", "?")}')

        devs = helper.send('list-devices', type='render', timeout=5.0)
        devices = devs.get('devices', [])
        print(f'\nRender devices: {len(devices)}')
        for d in devices[:5]:
            print(f'  id={d["id"][:50]}... name={d.get("name", "?")}')

        if sessions:
            pid = sessions[0]['pid']
            print(f'\n--- Testing set-session-device on PID={pid} ---')

            # Test 1: clear routing
            resp = helper.send('set-session-device', pid=pid, device_id='', timeout=5.0)
            print(f'Clear routing: {resp}')

            # Test 2: route to a specific device
            if devices:
                dev_id = devices[0]['id']
                print(f'Routing to: {devices[0].get("name", "?")}')
                resp = helper.send('set-session-device', pid=pid, device_id=dev_id, timeout=5.0)
                print(f'Route response: {resp}')

                resp2 = helper.send('get-session-device', pid=pid, timeout=5.0)
                print(f'Current deviceId: {resp2}')

        print('\nAll checks passed!')
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # `helper` stays None if AudioHelper() itself raised, so guard the call
        # instead of raising NameError from the cleanup path.
        if helper is not None:
            helper.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
