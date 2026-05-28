"""AudioHelper.exe subprocess wrapper — JSON protocol over stdin/stdout."""
import subprocess
import json
import threading
import queue
import os
import sys
import time


class AudioHelper:
    def __init__(self):
        # Find AudioHelper.exe
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle: search _MEIPASS (bundled) then next to EXE
            base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            exe = os.path.join(base, 'AudioHelper.exe')
            if not os.path.exists(exe):
                exe = os.path.join(os.path.dirname(sys.executable), 'AudioHelper.exe')
        else:
            base = os.path.dirname(os.path.abspath(__file__))
            # In dev, look relative to project root
            search_paths = [
                os.path.join(base, 'AudioHelper.exe'),
                os.path.join(base, '..', 'bin', 'AudioHelper.exe'),
                os.path.join(base, '..', 'audiocenter', 'bin', 'AudioHelper.exe'),
                os.path.join(base, '..', 'audiocenter', 'src-tauri', 'binaries', 'AudioHelper.exe'),
            ]
            exe = None
            for p in search_paths:
                if os.path.exists(p):
                    exe = p
                    break
            if exe is None:
                exe = os.path.join(base, 'binaries', 'AudioHelper.exe')
            if not os.path.exists(exe):
                exe = os.path.join(base, 'AudioHelper.exe')

        if not os.path.exists(exe):
            raise FileNotFoundError(f"找不到 AudioHelper.exe，搜索路径: {base}")

        self.process = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        self._lock = threading.Lock()
        self._response_queue: queue.Queue = queue.Queue()
        self._alive = True

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        try:
            for line in self.process.stdout:
                if not line.strip():
                    continue
                # Strip UTF-8 BOM if present (Python 3.14+ rejects BOM in json.loads)
                if line.startswith('﻿'):
                    line = line[1:]
                try:
                    resp = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._response_queue.put(resp)
        except Exception:
            pass
        finally:
            self._alive = False

    def send(self, cmd: str, timeout: float = 5.0, **kwargs) -> dict:
        """Send a command and return the response dict (raises on timeout)."""
        with self._lock:
            msg = {'cmd': cmd}
            msg.update(kwargs)
            try:
                self.process.stdin.write(json.dumps(msg, ensure_ascii=False) + '\n')
                self.process.stdin.flush()
            except Exception as e:
                raise RuntimeError(f"写入 AudioHelper 失败: {e}")

            try:
                return self._response_queue.get(timeout=timeout)
            except queue.Empty:
                raise TimeoutError(f"命令 '{cmd}' 超时 ({timeout}s)")

    def close(self):
        self._alive = False
        try:
            self.process.terminate()
        except Exception:
            pass

    def __del__(self):
        self.close()
