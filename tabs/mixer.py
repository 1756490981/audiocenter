"""Volume mixer tab — master volume + per-session sliders with device routing."""
import customtkinter as ctk
import threading
from iconutil import get_icon_ctk
from themecolors import C, apply_widget_theme

MMDEVAPI_TOKEN = '\\\\?\\SWD#MMDEVAPI#'
DEVINTERFACE_AUDIO_RENDER = '#{e6327cad-dcec-4949-ae8a-991e976a79d2}'
DEVINTERFACE_AUDIO_CAPTURE = '#{2eef81be-33fa-4800-9670-1cd474972c3f}'


def _unpack_device_id(device_id: str) -> str:
    """Strip MMDEVAPI token and GUID suffix, matching C# UnpackDeviceId."""
    if not device_id:
        return ''
    if device_id.startswith(MMDEVAPI_TOKEN):
        device_id = device_id[len(MMDEVAPI_TOKEN):]
    if device_id.endswith(DEVINTERFACE_AUDIO_RENDER):
        device_id = device_id[:-len(DEVINTERFACE_AUDIO_RENDER)]
    if device_id.endswith(DEVINTERFACE_AUDIO_CAPTURE):
        device_id = device_id[:-len(DEVINTERFACE_AUDIO_CAPTURE)]
    return device_id


class VolumeMixerTab(ctk.CTkFrame):
    def __init__(self, parent, helper):
        super().__init__(parent, fg_color='transparent')
        self.helper = helper
        self._devices: list[dict] = []
        self._session_frames: dict[int, ctk.CTkFrame] = {}
        self._dragging: set[int] = set()
        self._master_dragging = False
        self._alive = True

        # ── master volume ──
        master_frame = ctk.CTkFrame(self, fg_color='#14142e', corner_radius=10,
                                     border_width=1, border_color='#1e1e3a')
        master_frame.pack(fill='x', padx=12, pady=(12, 4))

        header = ctk.CTkFrame(master_frame, fg_color='transparent')
        header.pack(fill='x', padx=12, pady=(10, 2))
        ctk.CTkLabel(header, text='主音量', font=('Microsoft YaHei UI', 12),
                     text_color='#999999').pack(side='left')
        self._master_dev_label = ctk.CTkLabel(header, text='系统默认',
                                               font=('Microsoft YaHei UI', 13),
                                               text_color='#666666')
        self._master_dev_label.pack(side='right')

        row = ctk.CTkFrame(master_frame, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=(4, 10))

        self._master_mute_var = ctk.BooleanVar(value=False)
        self._master_mute_btn = ctk.CTkButton(
            row, text='🔊', width=28, height=28, fg_color='transparent',
            hover_color='#222244', font=('Segoe UI', 14),
            command=self._toggle_master_mute)
        self._master_mute_btn.pack(side='left')

        self._master_slider = ctk.CTkSlider(
            row, from_=0, to=100, width=200, height=16,
            fg_color='#1a1a3a', progress_color='#3b82f6',
            button_color='#3b82f6', button_hover_color='#6090f0',
            command=self._on_master_slider)
        self._master_slider.pack(side='left', fill='x', expand=True, padx=8)
        self._master_slider.bind('<Button-1>', lambda e: setattr(self, '_master_dragging', True), add='+')
        self._master_slider.bind('<ButtonRelease-1>', lambda e: setattr(self, '_master_dragging', False), add='+')

        self._master_val = ctk.CTkLabel(row, text='100', width=28,
                                         font=('Microsoft YaHei UI', 13),
                                         text_color='#888888')
        self._master_val.pack(side='right')

        # ── session list (scrollable) ──
        self._session_area = ctk.CTkScrollableFrame(
            self, fg_color='transparent', scrollbar_button_color='#222244',
            scrollbar_button_hover_color='#333355')
        self._session_area.pack(fill='both', expand=True, padx=12, pady=4)

        self._empty_label = ctk.CTkLabel(
            self._session_area, text='没有正在播放音频的应用',
            font=('Microsoft YaHei UI', 12), text_color='#444444')
        self._empty_label.pack(pady=40)

        # Start background refresh thread
        self._refresh_thread = threading.Thread(target=self._bg_refresh, daemon=True)
        self._refresh_thread.start()

    def destroy(self):
        self._alive = False
        super().destroy()

    # ── background refresh ──
    def _bg_refresh(self):
        import time
        while self._alive:
            try:
                vol = self.helper.send('get-master-volume', timeout=2.0)
                devs = self.helper.send('list-devices', type='render', timeout=2.0)
                sess = self.helper.send('list-sessions', timeout=2.0)
                # Schedule UI update on main thread
                self.after(0, self._update_ui, vol, devs, sess)
            except Exception:
                pass
            time.sleep(1.0)

    def _update_ui(self, vol, devs, sess):
        if not self._alive:
            return
        # Master (skip if user is dragging)
        if not self._master_dragging:
            self._master_slider.set(vol.get('volume', 100))
            self._master_val.configure(text=str(vol.get('volume', 100)))
        self._master_mute_var.set(vol.get('muted', False))
        self._master_mute_btn.configure(text='🔇' if vol.get('muted') else '🔊')

        # Devices for dropdowns
        self._devices = [d for d in devs.get('devices', []) if d.get('state') == 'active']
        default_dev = next((d for d in devs.get('devices', []) if d.get('isDefault')), None)
        if default_dev:
            self._master_dev_label.configure(text=default_dev.get('name', '系统默认'))

        # Sessions (exclude system sounds PID=0)
        incoming = [s for s in sess.get('sessions', []) if s['pid'] != 0]
        incoming_pids = {s['pid'] for s in incoming}

        for pid in list(self._session_frames):
            if pid not in incoming_pids:
                self._session_frames[pid].destroy()
                del self._session_frames[pid]

        if not incoming:
            self._empty_label.pack(pady=40)
        else:
            self._empty_label.pack_forget()

        for s in incoming:
            pid = s['pid']
            if pid in self._dragging:
                continue
            self._render_session(s)

    def _render_session(self, s: dict):
        pid = s['pid']
        name = s.get('displayName', 'Unknown')
        volume = s.get('volume', 100)
        muted = s.get('muted', False)
        device_id = s.get('deviceId') or ''

        if pid in self._session_frames:
            frame = self._session_frames[pid]
            children = frame.winfo_children()
            if len(children) >= 2:
                top = children[0]
                bottom = children[1]
                # Update slider
                slider = bottom.winfo_children()[0]
                if isinstance(slider, ctk.CTkSlider):
                    slider.set(volume)
                # Update value label (last child of top)
                val_lbl = top.winfo_children()[-1]
                if isinstance(val_lbl, ctk.CTkLabel):
                    val_lbl.configure(text=str(volume))
                # Update device dropdown (last child of bottom)
                dev_menu = bottom.winfo_children()[-1]
                if isinstance(dev_menu, ctk.CTkOptionMenu):
                    dev_names = ['默认'] + [d.get('name', '') for d in self._devices]
                    dev_ids_unpacked = [''] + [_unpack_device_id(d.get('id', '')) for d in self._devices]
                    try:
                        idx = dev_ids_unpacked.index(device_id) if device_id in dev_ids_unpacked else 0
                    except ValueError:
                        idx = 0
                    dev_menu.configure(values=dev_names,
                                       command=lambda choice: self._on_session_device(pid, choice))
                    dev_menu.set(dev_names[idx])
            return

        # New session frame
        frame = ctk.CTkFrame(self._session_area, fg_color='#14142e',
                              corner_radius=8, border_width=1,
                              border_color='#1e1e3a')
        frame.pack(fill='x', pady=2)

        top = ctk.CTkFrame(frame, fg_color='transparent')
        top.pack(fill='x', padx=8, pady=(8, 0))

        mute_var = ctk.BooleanVar(value=muted)
        mute_btn = ctk.CTkButton(
            top, text='🔇' if muted else '🔊', width=24, height=24,
            fg_color='transparent', hover_color='#222244',
            font=('Segoe UI', 12))
        mute_btn.configure(command=lambda b=mute_btn, v=mute_var: self._toggle_session_mute(pid, b, v))
        mute_btn.pack(side='left')

        # App icon (from session's icon path)
        icon_path = s.get('icon')
        ctk_icon = get_icon_ctk(icon_path, 20)
        if ctk_icon:
            icon_lbl = ctk.CTkLabel(top, image=ctk_icon, text='', width=20, height=20)
            icon_lbl.pack(side='left', padx=(2, 0))
            frame._icon_ref = ctk_icon  # prevent GC

        ctk.CTkLabel(top, text=name, font=('Microsoft YaHei UI', 12),
                     text_color='#cccccc', anchor='w').pack(side='left', fill='x', expand=True, padx=(4 if ctk_icon else 6, 6))

        val_lbl = ctk.CTkLabel(top, text=str(volume), font=('Microsoft YaHei UI', 13),
                                text_color='#777777', width=24)
        val_lbl.pack(side='right')

        bottom = ctk.CTkFrame(frame, fg_color='transparent')
        bottom.pack(fill='x', padx=8, pady=(2, 8))

        slider = ctk.CTkSlider(
            bottom, from_=0, to=100, width=200, height=14,
            fg_color='#1a1a3a', progress_color='#3b82f6',
            button_color='#3b82f6', button_hover_color='#6090f0',
            command=lambda v, p=pid: self._on_session_slider(p, v))
        slider.set(volume)
        slider.pack(side='left', fill='x', expand=True)

        slider.bind('<Button-1>', lambda e, p=pid: self._dragging.add(p), add='+')
        slider.bind('<ButtonRelease-1>', lambda e, p=pid: self._dragging.discard(p), add='+')

        # Device selector
        dev_names = ['默认'] + [d.get('name', '') for d in self._devices]
        # Packed IDs (sent to other commands), and unpacked IDs (for matching session + set-session-device)
        dev_ids_packed = [''] + [d.get('id', '') for d in self._devices]
        dev_ids_unpacked = [''] + [_unpack_device_id(d.get('id', '')) for d in self._devices]
        # Session deviceId is unpacked; match against unpacked list
        try:
            idx = dev_ids_unpacked.index(device_id) if device_id in dev_ids_unpacked else 0
        except ValueError:
            idx = 0

        dev_var = ctk.StringVar(value=dev_names[idx])
        dev_menu = ctk.CTkOptionMenu(
            bottom, values=dev_names, variable=dev_var,
            width=110, height=22, font=('Microsoft YaHei UI', 13),
            fg_color='#1a1a3a', button_color='#1a1a3a',
            button_hover_color='#2a2a4a', text_color='#999999',
            dropdown_fg_color='#14142e', dropdown_text_color='#999999',
            dropdown_hover_color='#222244',
            command=lambda choice: self._on_session_device(pid, choice))
        dev_menu.pack(side='right', padx=(6, 0))

        self._session_frames[pid] = frame

    # ── master volume (deferred to thread) ──
    def _on_master_slider(self, val):
        v = int(float(val))
        self._master_val.configure(text=str(v))
        threading.Thread(target=lambda: self.helper.send('set-master-volume', volume=v), daemon=True).start()

    def _toggle_master_mute(self):
        new = not self._master_mute_var.get()
        self._master_mute_var.set(new)
        self._master_mute_btn.configure(text='🔇' if new else '🔊')
        threading.Thread(target=lambda: self.helper.send('set-master-mute', mute=new), daemon=True).start()

    # ── session controls (deferred to thread) ──
    def _on_session_slider(self, pid, val):
        v = int(float(val))
        # Update label immediately
        frame = self._session_frames.get(pid)
        if frame:
            children = frame.winfo_children()
            if children:
                top = children[0]
                val_lbl = top.winfo_children()[-1]
                if isinstance(val_lbl, ctk.CTkLabel):
                    val_lbl.configure(text=str(v))
        threading.Thread(target=lambda: self.helper.send('set-session-volume', pid=pid, volume=v), daemon=True).start()

    def _toggle_session_mute(self, pid, btn, var):
        new = not var.get()
        var.set(new)
        btn.configure(text='🔇' if new else '🔊')
        threading.Thread(target=lambda: self.helper.send('set-session-mute', pid=pid, mute=new), daemon=True).start()

    def _on_session_device(self, pid, device_name):
        """device_name is the display name ('默认' or device name). Look up unpacked ID from current device list."""
        dev_names = ['默认'] + [d.get('name', '') for d in self._devices]
        dev_ids_unpacked = [''] + [_unpack_device_id(d.get('id', '')) for d in self._devices]
        try:
            idx = dev_names.index(device_name) if device_name in dev_names else 0
        except ValueError:
            idx = 0
        device_id = dev_ids_unpacked[idx]

        def _send():
            try:
                self.helper.send('set-session-device', pid=pid, device_id=device_id or '')
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()

    def apply_theme(self, colors):
        apply_widget_theme(self, colors)
