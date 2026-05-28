"""Developer tool — generate license keys for AudioCenter.

Usage:
    python activate.py <machine_id>
    python activate.py --show-id    # show this machine's ID
"""
import sys
import os

# Add project dir to path so we can import license
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from license import get_machine_id, generate_license


def main():
    if len(sys.argv) < 2:
        print('用法:')
        print('  python activate.py <机器码>      生成授权码')
        print('  python activate.py --show-id     查看本机机器码')
        return

    arg = sys.argv[1]

    if arg == '--show-id':
        mid = get_machine_id()
        print(f'本机机器码: {mid}')
        return

    machine_id = arg.strip().upper()
    if len(machine_id) != 16:
        print(f'错误：机器码应为 16 位，当前 {len(machine_id)} 位')
        return

    license_str = generate_license(machine_id)
    print(f'机器码: {machine_id}')
    print(f'授权码: {license_str}')
    print()
    print(f'将上面的授权码保存为 license.dat 文件，放到 AudioCenter.exe 同目录即可。')


if __name__ == '__main__':
    main()
