# -*- coding: utf-8 -*-
"""Studio One ASIO one-click repair tab.

Auto-detect ASIO drivers, match sample rate & buffer,
one-click fix AudioEngine.settings and restart Studio One.
"""
import os
import re
import shutil
import time
import ctypes
import subprocess
import threading
import warnings
import xml.etree.ElementTree as ET
import winreg
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="pycaw")

import customtkinter as ctk
from pycaw.pycaw import AudioUtilities
from themecolors import C, apply_widget_theme

# ── Paths ────────────────────────────────────────────
APPDATA = Path(os.environ["APPDATA"])
CONFIG_DIR = APPDATA / "audio-device-locker"
BACKUP_DIR = CONFIG_DIR / "backups"

STUDIO_PROC_NAMES = ["Studio Pro.exe", "Studio One.exe"]

SAMPLE_RATES = ["44100", "48000", "96000"]
BUFFER_SIZES = ["64", "128", "256", "512", "1024"]

# Suppress console windows from subprocess calls
_NO_WIN = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0x08000000


# ── Utilities ────────────────────────────────────────
def find_settings_dir():
    dirs = []
    for vendor in ["PreSonus", "Fender"]:
        base = APPDATA / vendor
        if not base.exists():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            m = re.match(r"^Studio\s*(?:One|Pro)\s*(\d+)$", d.name, re.IGNORECASE)
            if m:
                dirs.append((int(m.group(1)), d))
    dirs.sort(key=lambda x: x[0], reverse=True)
    return dirs[0][1] if dirs else None


def find_studio_exe():
    exes = []
    search_bases = ["C:/Program Files", "C:/Program Files (x86)"]
    for vendor in ["PreSonus", "Fender"]:
        for base in list(search_bases):
            v = Path(base) / vendor
            if v.exists():
                search_bases.append(str(v))
    for base in search_bases:
        if not os.path.exists(base):
            continue
        for d in os.listdir(base):
            m = re.match(r"^Studio\s*(?:One|Pro)\s*(\d+)$", d, re.IGNORECASE)
            if not m:
                continue
            full = Path(base) / d
            for name in STUDIO_PROC_NAMES:
                exe = full / name
                if exe.exists():
                    exes.append((int(m.group(1)), exe))
    exes.sort(key=lambda x: x[0], reverse=True)
    return exes[0][1] if exes else None


def is_studio_running():
    for name in STUDIO_PROC_NAMES:
        try:
            r = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {name}"],
                capture_output=True, text=True,
                creationflags=_NO_WIN,
            )
            if name.lower() in r.stdout.lower():
                return name
        except Exception:
            pass
    return None


def get_studio_process():
    """Return the running Studio process name, or None."""
    return is_studio_running()


# ── ASIO Driver Enumeration ──────────────────────────
def _get_active_endpoint_names():
    names = set()
    try:
        for d in AudioUtilities.GetAllDevices():
            try:
                if d.FriendlyName and d.state.value == 1:
                    names.add(d.FriendlyName)
            except Exception:
                continue
    except Exception:
        pass
    return names


def enum_asio_drivers():
    drivers = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ASIO")
    except OSError:
        return drivers

    active_endpoints = _get_active_endpoint_names()

    i = 0
    while True:
        try:
            key_name = winreg.EnumKey(root, i)
            key = winreg.OpenKey(root, key_name)
            clsid = winreg.QueryValueEx(key, "CLSID")[0]
            desc = ""
            try:
                desc = winreg.QueryValueEx(key, "Description")[0]
            except OSError:
                desc = key_name
            winreg.CloseKey(key)

            desc_words = set(re.sub(r"[^\w\s]", " ", desc.lower()).split())
            key_words = set(re.sub(r"[^\w\s]", " ", key_name.lower()).split())
            match_words = desc_words | key_words
            connected = False
            if match_words:
                for ep in active_endpoints:
                    ep_words = set(re.sub(r"[^\w\s]", " ", ep.lower()).split())
                    common = len(match_words & ep_words)
                    if common >= max(2, len(match_words) * 0.8):
                        connected = True
                        break

            drivers.append({
                "name": desc,
                "key_name": key_name,
                "clsid": clsid,
                "connected": connected,
            })
            i += 1
        except OSError:
            break

    winreg.CloseKey(root)
    drivers.sort(key=lambda d: (not d["connected"], d["name"]))
    return drivers


# ── AudioEngine.settings Operations ──────────────────
def get_settings_path():
    d = find_settings_dir()
    return d / "x64" / "AudioEngine.settings" if d else None


def read_audio_engine():
    p = get_settings_path()
    if not p or not p.exists():
        return None
    tree = ET.parse(str(p))
    root = tree.getroot()
    attrs = root.find(".//Attributes")
    if attrs is None:
        return None
    return {
        "masterDevice": attrs.get("masterDevice", ""),
        "sampleRate": attrs.get("sampleRate", "48000"),
        "deviceBlockSize": attrs.get("deviceBlockSize", "128"),
        "failedDevices": attrs.get("failedDevices", ""),
        "floatType": attrs.get("floatType", "0"),
        "dropOutProtectionLevel": attrs.get("dropOutProtectionLevel", "0"),
        "suspendInBackground": attrs.get("suspendInBackground", "0"),
        "silencePolicy": attrs.get("silencePolicy", "1"),
        "useEfficiencyCores": attrs.get("useEfficiencyCores", "0"),
        "file_path": str(p),
        "settings_dir": str(p.parent.parent),
    }


def write_audio_engine(master_device, sample_rate="48000", block_size="128",
                       failed_devices="", **kwargs):
    p = get_settings_path()
    if not p:
        return False

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if p.exists():
        shutil.copy2(p, BACKUP_DIR / f"AudioEngine_before_fix_{ts}.settings")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Settings xmlns:x="https://ccl.dev/xml" name="AudioEngine" version="1">\n'
        '\t<Section path="AudioEngine">\n'
        f'\t\t<Attributes sampleRate="{sample_rate}"'
        f' masterDevice="{master_device}"'
        f' deviceBlockSize="{block_size}"'
        f' dropOutProtectionLevel="{kwargs.get("dropOutProtectionLevel", "0")}"'
        f' floatType="{kwargs.get("floatType", "0")}"'
        f' suspendInBackground="{kwargs.get("suspendInBackground", "0")}"'
        f' silencePolicy="{kwargs.get("silencePolicy", "1")}"'
        f' useEfficiencyCores="{kwargs.get("useEfficiencyCores", "0")}"'
        f' failedDevices="{failed_devices}"/>\n'
        '\t</Section>\n'
        '</Settings>\n'
    )
    p.write_text(xml, encoding="utf-8")
    return True


def _graceful_kill_studio(proc_name):
    """Try WM_CLOSE first, force-kill only if it doesn't respond."""
    # Find Studio One windows
    hwnds = []
    def _enum_cb(hwnd, _lparam):
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 260)
        if buf.value and ('Studio' in buf.value or 'studio' in buf.value.lower()):
            hwnds.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)

    # Bring Studio to foreground so user sees any save dialog
    for hwnd in hwnds:
        # Restore if minimized
        SW_RESTORE = 9
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        try:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    # Send WM_CLOSE to Studio windows
    WM_CLOSE = 0x0010
    for hwnd in hwnds:
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    # Wait for graceful close — rapid polling for fast response
    for _ in range(100):  # ~10 seconds, 0.1s intervals
        if not is_studio_running():
            return True
        time.sleep(0.1)

    # Still running — force kill
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", proc_name],
            capture_output=True, timeout=10,
            creationflags=_NO_WIN,
        )
    except Exception:
        pass

    for _ in range(30):  # ~3 seconds
        if not is_studio_running():
            break
        time.sleep(0.1)
    return not is_studio_running()


def restart_studio():
    proc = get_studio_process()
    exe = find_studio_exe()

    if proc:
        _graceful_kill_studio(proc)

    if exe and exe.exists():
        subprocess.Popen([str(exe)], creationflags=_NO_WIN)
        return True
    return False


# ── Tab GUI ──────────────────────────────────────────
class StudioOneTab(ctk.CTkFrame):
    def __init__(self, parent, helper):
        super().__init__(parent, fg_color='transparent')

        self.asio_drivers = []
        self.current_cfg = None
        self.selected_driver = None

        self._build_ui()
        # Defer heavy init to keep startup fast
        self.after(50, self._refresh)

    def _build_ui(self):
        # ── Status ───────────────────────────────────
        ctk.CTkLabel(
            self, text="Studio One 状态",
            font=('Microsoft YaHei UI', 13, 'bold'),
            text_color=C['text_primary'],
        ).pack(padx=12, pady=(12, 4), anchor="w")
        self.status_box = ctk.CTkTextbox(
            self, height=50, wrap="word", state="disabled",
            fg_color=C['card_bg'], text_color=C['text_primary'],
            font=('Microsoft YaHei UI', 12),
        )
        self.status_box.pack(padx=12, fill="x")

        # ── ASIO Drivers ─────────────────────────────
        ctk.CTkLabel(
            self, text="ASIO 驱动列表（绿=在线，灰=离线，点击选中）",
            font=('Microsoft YaHei UI', 13, 'bold'),
            text_color=C['text_primary'],
        ).pack(padx=12, pady=(12, 4), anchor="w")

        self.driver_list = ctk.CTkScrollableFrame(
            self, height=130, fg_color='transparent',
            scrollbar_button_color=C['scrollbar'],
            scrollbar_button_hover_color=C['btn_hover'],
        )
        self.driver_list.pack(padx=12, fill="x")

        # ── Sample Rate + Buffer ─────────────────────
        params = ctk.CTkFrame(self, fg_color="transparent")
        params.pack(padx=12, pady=(10, 0), fill="x")

        ctk.CTkLabel(params, text="采样率:",
                     font=('Microsoft YaHei UI', 12),
                     text_color=C['text_secondary']).pack(side="left", padx=(0, 6))
        self.sr_var = ctk.StringVar(value="48000")
        self.sr_menu = ctk.CTkOptionMenu(
            params, values=SAMPLE_RATES, variable=self.sr_var, width=90,
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], button_color=C['btn_bg'],
            button_hover_color=C['btn_hover'],
            dropdown_fg_color=C['dropdown_bg'],
        )
        self.sr_menu.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(params, text="缓冲区:",
                     font=('Microsoft YaHei UI', 12),
                     text_color=C['text_secondary']).pack(side="left", padx=(0, 6))
        self.bs_var = ctk.StringVar(value="128")
        self.bs_menu = ctk.CTkOptionMenu(
            params, values=BUFFER_SIZES, variable=self.bs_var, width=90,
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], button_color=C['btn_bg'],
            button_hover_color=C['btn_hover'],
            dropdown_fg_color=C['dropdown_bg'],
        )
        self.bs_menu.pack(side="left")

        # ── Current Config ───────────────────────────
        ctk.CTkLabel(
            self, text="当前配置",
            font=('Microsoft YaHei UI', 13, 'bold'),
            text_color=C['text_primary'],
        ).pack(padx=12, pady=(12, 4), anchor="w")
        self.cfg_box = ctk.CTkTextbox(
            self, height=65, wrap="word", state="disabled",
            fg_color=C['card_bg'], text_color=C['text_primary'],
            font=('Microsoft YaHei UI', 12),
        )
        self.cfg_box.pack(padx=12, fill="x")

        # ── Big Fix Button ───────────────────────────
        self.fix_btn = ctk.CTkButton(
            self, text="一键修复并重启 Studio One",
            width=400, height=50,
            font=('Microsoft YaHei UI', 15, 'bold'),
            fg_color=C['danger'], hover_color=C['danger_hover'],
            command=self._on_fix,
        )
        self.fix_btn.pack(padx=12, pady=(14, 6))

        # ── Sub buttons ──────────────────────────────
        sub_btns = ctk.CTkFrame(self, fg_color="transparent")
        sub_btns.pack(padx=12, pady=(2, 0), fill="x")

        ctk.CTkButton(
            sub_btns, text="刷新", width=80, height=28,
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], hover_color=C['btn_hover'],
            text_color=C['text_secondary'],
            command=self._refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            sub_btns, text="仅修复（不重启）",
            width=120, height=28,
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], hover_color=C['btn_hover'],
            text_color=C['text_secondary'],
            command=self._on_fix_only,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            sub_btns, text="重置音频配置",
            width=120, height=28,
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], hover_color=C['btn_hover'],
            text_color=C['warning'],
            command=self._on_reset,
        ).pack(side="left")

        # ── Bottom Status ────────────────────────────
        self.bottom_var = ctk.StringVar(value="就绪")
        ctk.CTkLabel(
            self, textvariable=self.bottom_var,
            font=('Microsoft YaHei UI', 12),
            text_color=C['text_dim'],
        ).pack(padx=12, pady=(10, 4), anchor="w")

    def _set_text(self, box, text):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _refresh(self):
        running = is_studio_running()
        s_dir = find_settings_dir()
        exe = find_studio_exe()
        lines = [
            f"  Studio One: {'运行中' if running else '未运行'}",
        ]
        if s_dir:
            lines.append(f"  设置目录: {s_dir}")
        else:
            lines.append("  未检测到 Studio One")
        if exe:
            lines.append(f"  程序路径: {exe}")
        self._set_text(self.status_box, "\n".join(lines))

        self.asio_drivers = enum_asio_drivers()

        # Auto-select: failed device first, else first online
        current_cfg = read_audio_engine()
        failed = current_cfg.get("failedDevices", "") if current_cfg else ""
        if not self.selected_driver and self.asio_drivers:
            for drv in self.asio_drivers:
                if failed and drv["clsid"].lower() == failed.lower():
                    self.selected_driver = drv
                    break
            if not self.selected_driver:
                for drv in self.asio_drivers:
                    if drv["connected"]:
                        self.selected_driver = drv
                        break

        for w in self.driver_list.winfo_children():
            w.destroy()

        for drv in self.asio_drivers:
            status = "[在线]" if drv["connected"] else "[离线]"
            color = "#22c55e" if drv["connected"] else "#6b7280"
            frame = ctk.CTkFrame(self.driver_list, fg_color="transparent")
            frame.pack(fill="x", pady=1)

            ctk.CTkLabel(
                frame,
                text=f"  {status}  {drv['name']}",
                font=('Microsoft YaHei UI', 12),
                text_color=color,
            ).pack(side="left")

            is_sel = (
                self.selected_driver
                and self.selected_driver["clsid"] == drv["clsid"]
            )
            sel_text = "已选中" if is_sel else "选中"
            ctk.CTkButton(
                frame, text=sel_text, width=70, height=24,
                font=('Microsoft YaHei UI', 11),
                fg_color=C['accent'] if is_sel else C['btn_bg'],
                hover_color='#6090f0' if is_sel else C['btn_hover'],
                command=lambda d=drv: self._select_driver(d),
            ).pack(side="right", padx=4)

        self.current_cfg = current_cfg
        if self.current_cfg:
            self._set_text(
                self.cfg_box,
                f"  ASIO: {self.current_cfg['masterDevice']}\n"
                f"  采样率: {self.current_cfg['sampleRate']} Hz  |  "
                f"缓冲区: {self.current_cfg['deviceBlockSize']} samples\n"
                f"  失败设备: {self.current_cfg['failedDevices'] or '无'}",
            )
            sr = self.current_cfg.get("sampleRate", "48000")
            if sr in SAMPLE_RATES:
                self.sr_var.set(sr)
            bs = self.current_cfg.get("deviceBlockSize", "128")
            if bs in BUFFER_SIZES:
                self.bs_var.set(bs)
        else:
            self._set_text(self.cfg_box, "  未找到 AudioEngine.settings")

        if self.selected_driver:
            online = "在线" if self.selected_driver["connected"] else "离线"
            warn = "" if self.selected_driver["connected"] else "（设备未连接！）"
            self.bottom_var.set(
                f"目标: {self.selected_driver['name']} [{online}]{warn}"
                f"  |  {self.sr_var.get()}Hz / {self.bs_var.get()} samples"
            )
        else:
            self.bottom_var.set("请在 ASIO 列表中选中要修复的声卡")

    def _select_driver(self, drv):
        self.selected_driver = drv
        self._refresh()

    def apply_theme(self, colors):
        """Update colors when theme toggles."""
        apply_widget_theme(self, colors)
        # Also refresh the driver list (rebuilt on _refresh, but live updates help)
        self._refresh()

    def _do_fix(self):
        if not self.selected_driver:
            return False, "请先在列表中选择目标声卡"

        cfg = self.current_cfg or {}
        ok = write_audio_engine(
            master_device=self.selected_driver["clsid"],
            sample_rate=self.sr_var.get(),
            block_size=self.bs_var.get(),
            failed_devices="",
            floatType=cfg.get("floatType", "0"),
            dropOutProtectionLevel=cfg.get("dropOutProtectionLevel", "0"),
            suspendInBackground=cfg.get("suspendInBackground", "0"),
            silencePolicy=cfg.get("silencePolicy", "1"),
            useEfficiencyCores=cfg.get("useEfficiencyCores", "0"),
        )
        if not ok:
            return False, "写入配置文件失败"
        return True, self.selected_driver["clsid"]

    def _on_reset(self):
        p = get_settings_path()
        if not p or not p.exists():
            self.bottom_var.set("配置文件不存在，无需重置")
            return

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(p, BACKUP_DIR / f"AudioEngine_reset_{ts}.settings")

        p.unlink()
        self._refresh()
        self.bottom_var.set(
            "已删除 AudioEngine.settings。下次启动 Studio One 时将进入音频设置向导，"
            "请手动选择你的声卡（只需要做一次）。"
        )

    def _on_fix_only(self):
        ok, msg = self._do_fix()
        if ok:
            self._refresh()
            self.bottom_var.set("配置已修复，请重启 Studio One 使其生效。")
        else:
            self.bottom_var.set(msg)

    def _on_fix(self):
        if not self.selected_driver:
            self.bottom_var.set("请先在列表中选择目标声卡")
            return

        if not self.selected_driver["connected"]:
            self.bottom_var.set(
                f"警告：{self.selected_driver['name']} 当前离线，请先连接设备。"
            )
            return

        # Step 1: Close Studio gracefully before writing config
        proc = get_studio_process()
        if proc:
            self.bottom_var.set("正在关闭 Studio...")
            self.update()
            _graceful_kill_studio(proc)

        # Step 2: Write config
        ok, msg = self._do_fix()
        if not ok:
            self.bottom_var.set(msg)
            return

        self.bottom_var.set("正在重启 Studio...")
        self.update()

        # Step 3: Restart
        if restart_studio():
            self._refresh()
            self.bottom_var.set(
                f"修复完成！已切换到 {self.selected_driver['name']} "
                f"@ {self.sr_var.get()}Hz / {self.bs_var.get()} samples"
            )
        else:
            self._refresh()
            self.bottom_var.set("配置已修复，请手动打开 Studio。")
