"""Playback device tab — list render devices, set default, volume, format, enable/disable."""
import customtkinter as ctk
import threading
from tkinter import Menu
from themecolors import C, apply_widget_theme


STATE_MAP = {
    'active': '就绪', 'disabled': '已禁用',
    'not-present': '不存在', 'unplugged': '未插入', 'unknown': '未知',
}

SAMPLE_RATES = [44100, 48000, 96000, 192000]
BIT_DEPTHS = [16, 24, 32]
CHANNELS = [1, 2]
PRESETS = [
    ('CD 音质', 44100, 16, 2),
    ('DVD 音质', 48000, 16, 2),
    ('录音室', 48000, 24, 2),
    ('高解析度', 96000, 24, 2),
    ('发烧级', 192000, 24, 2),
]


class PlaybackDeviceTab(ctk.CTkFrame):
    def __init__(self, parent, helper):
        super().__init__(parent, fg_color='transparent')
        self.helper = helper
        self._devices: list[dict] = []
        self._volumes: dict[str, dict] = {}
        self._show_disabled = False
        self._device_frames: dict[str, ctk.CTkFrame] = {}
        self._alive = True

        # ── header ──
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=12, pady=(12, 4))
        ctk.CTkLabel(header, text='选择默认播放设备', font=('Microsoft YaHei UI', 12),
                     text_color='#888888').pack(side='left')
        ctk.CTkButton(header, text='↻', width=28, height=28,
                      fg_color='transparent', hover_color='#222244',
                      font=('Segoe UI', 16), text_color='#888888',
                      command=self.refresh).pack(side='right')

        # ── scrollable device list ──
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color='transparent', scrollbar_button_color='#222244',
            scrollbar_button_hover_color='#333355')
        self._scroll.pack(fill='both', expand=True, padx=12, pady=4)

        # ── disabled toggle ──
        self._disabled_header = ctk.CTkFrame(self, fg_color='transparent')
        self._disabled_header.pack(fill='x', padx=12, pady=(0, 6))
        self._disabled_btn = None

        self.refresh()

        # Background auto-refresh
        self._refresh_thread = threading.Thread(target=self._bg_refresh, daemon=True)
        self._refresh_thread.start()

    def destroy(self):
        self._alive = False
        super().destroy()

    def _bg_refresh(self):
        import time
        while self._alive:
            time.sleep(3.0)
            if not self._alive:
                break
            try:
                res = self.helper.send('list-devices', type='render', timeout=2.0)
                devices = res.get('devices', [])
            except Exception:
                continue
            # Check if device list changed (new/removed devices or state changes)
            current_ids = {d.get('id'): d.get('state') for d in devices}
            prev_ids = {d.get('id'): d.get('state') for d in self._devices}
            if current_ids != prev_ids:
                self.after(0, self.refresh)
                continue
            # Device list unchanged — just refresh volumes
            volumes = {}
            for d in devices:
                if d.get('state') != 'active':
                    continue
                try:
                    r = self.helper.send('get-device-volume', id=d['id'], timeout=2.0)
                    volumes[d['id']] = {
                        'volume': r.get('volume', 100),
                        'muted': r.get('muted', False),
                        'hasEndpointVolume': r.get('hasEndpointVolume', False),
                    }
                except Exception:
                    volumes[d['id']] = {'hasEndpointVolume': False}
            self.after(0, self._update_volumes, volumes)

    def refresh(self):
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        try:
            res = self.helper.send('list-devices', type='render', timeout=3.0)
            devices = res.get('devices', [])
        except Exception:
            return
        # Fetch volumes
        volumes = {}
        for d in devices:
            if d.get('state') != 'active':
                continue
            try:
                r = self.helper.send('get-device-volume', id=d['id'], timeout=2.0)
                volumes[d['id']] = {
                    'volume': r.get('volume', 100),
                    'muted': r.get('muted', False),
                    'hasEndpointVolume': r.get('hasEndpointVolume', False),
                }
            except Exception:
                volumes[d['id']] = {'hasEndpointVolume': False}
        self.after(0, self._apply_refresh, devices, volumes)

    def _apply_refresh(self, devices, volumes):
        self._devices = devices
        self._volumes = volumes
        self._render()

    def _render(self):
        # Clear existing
        for f in self._device_frames.values():
            f.destroy()
        self._device_frames.clear()

        active = [d for d in self._devices if d.get('state') == 'active']
        disabled = [d for d in self._devices if d.get('state') != 'active']

        for d in active:
            self._render_device(d)
        for d in disabled:
            self._render_device(d, hidden=not self._show_disabled)

        # Update disabled toggle
        if self._disabled_btn:
            self._disabled_btn.destroy()
        if disabled:
            label = f'▼ 已禁用设备 ({len(disabled)})' if self._show_disabled else f'▶ 已禁用设备 ({len(disabled)})'
            self._disabled_btn = ctk.CTkButton(
                self._disabled_header, text=label,
                font=('Microsoft YaHei UI', 12), text_color='#666666',
                fg_color='transparent', hover_color='#1a1a3a',
                anchor='w', command=self._toggle_disabled)
            self._disabled_btn.pack(fill='x')

    def _render_device(self, d: dict, hidden: bool = False):
        is_default = d.get('isDefault', False)
        vol = self._volumes.get(d['id'], {})

        frame = ctk.CTkFrame(self._scroll, fg_color='#14142e', corner_radius=8,
                              border_width=1,
                              border_color='#3b82f6' if is_default else '#1e1e3a')
        if not hidden:
            frame.pack(fill='x', pady=2)
        else:
            frame.pack_forget()

        # Top row: name + state + action
        top = ctk.CTkFrame(frame, fg_color='transparent')
        top.pack(fill='x', padx=10, pady=(10, 4))

        name_lbl = ctk.CTkLabel(top, text=d.get('name', ''), font=('Microsoft YaHei UI', 13),
                                 text_color='#cccccc', anchor='w')
        name_lbl.pack(side='left')

        if is_default:
            ctk.CTkLabel(top, text='默认', font=('Microsoft YaHei UI', 11),
                         text_color='#ffffff', fg_color='#3b82f6',
                         corner_radius=4, width=30, height=18).pack(side='right', padx=(4, 0))
        elif d.get('state') == 'active':
            ctk.CTkButton(top, text='设为默认', font=('Microsoft YaHei UI', 11),
                          text_color='#3b82f6', fg_color='transparent',
                          hover_color='#1a1a3a', width=60, height=22,
                          command=lambda did=d['id']: self._set_default(did)).pack(side='right')

        # State label
        state_text = STATE_MAP.get(d.get('state'), d.get('state', ''))
        ctk.CTkLabel(top, text=state_text, font=('Microsoft YaHei UI', 11),
                     text_color='#555555').pack(side='right', padx=(0, 8))

        # Volume row (if endpoint volume available)
        if vol.get('hasEndpointVolume'):
            vrow = ctk.CTkFrame(frame, fg_color='transparent')
            vrow.pack(fill='x', padx=10, pady=(2, 10))

            mute_var = ctk.BooleanVar(value=vol.get('muted', False))
            mute_btn = ctk.CTkButton(
                vrow, text='🔇' if vol.get('muted') else '🔊',
                width=24, height=24, fg_color='transparent',
                hover_color='#222244', font=('Segoe UI', 12),
                command=lambda did=d['id'], mv=mute_var, mb=None: self._toggle_mute(did, mv))
            mute_btn.pack(side='left')

            slider = ctk.CTkSlider(
                vrow, from_=0, to=100, width=200, height=14,
                fg_color='#1a1a3a', progress_color='#3b82f6',
                button_color='#3b82f6', button_hover_color='#6090f0')
            slider.set(vol.get('volume', 100))
            slider.pack(side='left', fill='x', expand=True, padx=8)

            val_lbl = ctk.CTkLabel(vrow, text=str(vol.get('volume', 100)),
                                     font=('Microsoft YaHei UI', 11), text_color='#777777',
                                     width=24)
            val_lbl.pack(side='right')
            # Set command after both slider and label exist
            slider.configure(command=lambda v, did=d['id'], lbl=val_lbl: self._set_volume(did, int(float(v)), lbl))

        # Right-click menu
        frame.bind('<Button-3>', lambda e, dev=d: self._context_menu(e, dev))
        for child in frame.winfo_children():
            child.bind('<Button-3>', lambda e, dev=d: self._context_menu(e, dev))
            for sub in child.winfo_children():
                sub.bind('<Button-3>', lambda e, dev=d: self._context_menu(e, dev))

        self._device_frames[d['id']] = frame

    def _set_default(self, device_id):
        def _run():
            try:
                self.helper.send('set-default-device', id=device_id, type='render', timeout=3.0)
            except Exception:
                pass
            self.after(200, self.refresh)
        threading.Thread(target=_run, daemon=True).start()

    def _set_volume(self, device_id, volume, label=None):
        if label:
            label.configure(text=str(volume))
        threading.Thread(target=lambda: self.helper.send('set-device-volume', id=device_id, volume=volume), daemon=True).start()

    def _update_volumes(self, volumes):
        """Update volume sliders and labels without rebuilding entire UI."""
        self._volumes = volumes
        for dev_id, vol in volumes.items():
            frame = self._device_frames.get(dev_id)
            if not frame or not frame.winfo_exists():
                continue
            children = frame.winfo_children()
            for child in children:
                # Find slider and label in the volume row
                for sub in child.winfo_children():
                    if isinstance(sub, ctk.CTkSlider):
                        sub.set(vol.get('volume', 100))
                    elif isinstance(sub, ctk.CTkLabel) and sub.cget('text').isdigit():
                        sub.configure(text=str(vol.get('volume', 100)))

    def _toggle_mute(self, device_id, mute_var):
        new = not mute_var.get()
        mute_var.set(new)
        threading.Thread(target=lambda: self.helper.send('set-device-mute', id=device_id, mute=new), daemon=True).start()

    def _toggle_disabled(self):
        self._show_disabled = not self._show_disabled
        self._render()

    def _context_menu(self, event, device):
        menu = Menu(self, tearoff=0, bg='#1a1a2e', fg='#cccccc',
                     activebackground='#2a2a4a', activeforeground='#ffffff',
                     font=('Microsoft YaHei UI', 12))
        if device.get('state') == 'active':
            menu.add_command(label='调整格式', command=lambda: self._show_format(device))
            menu.add_command(label='禁用', command=lambda: self._set_enabled(device['id'], False))
        else:
            menu.add_command(label='启用', command=lambda: self._set_enabled(device['id'], True))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _set_enabled(self, device_id, enabled):
        def _run():
            try:
                self.helper.send('set-device-enabled', id=device_id, enabled=enabled, timeout=3.0)
            except Exception:
                pass
            self.after(200, self.refresh)
        threading.Thread(target=_run, daemon=True).start()

    def apply_theme(self, colors):
        apply_widget_theme(self, colors)

    # ── format dialog ──
    def _show_format(self, device):
        dialog = ctk.CTkToplevel(self)
        dialog.title('调整格式')
        dialog.geometry('420x380')
        dialog.resizable(False, False)
        dialog.grab_set()
        _center_on_parent(dialog, self)

        ctk.CTkLabel(dialog, text=f'调整格式 — {device.get("name", "")}',
                     font=('Microsoft YaHei UI', 14, 'bold'),
                     text_color='#cccccc').pack(pady=(12, 8))

        # Loading label
        loading_lbl = ctk.CTkLabel(dialog, text='正在读取设备格式...',
                                    font=('Microsoft YaHei UI', 12),
                                    text_color='#888888')
        loading_lbl.pack(pady=20)

        # Build the form (initially hidden)
        form_frame = ctk.CTkFrame(dialog, fg_color='transparent')

        grid = ctk.CTkFrame(form_frame, fg_color='transparent')
        grid.pack(fill='x', padx=16, pady=8)

        sr_var = ctk.IntVar(value=48000)
        bd_var = ctk.IntVar(value=24)
        ch_var = ctk.IntVar(value=2)

        ctk.CTkLabel(grid, text='采样率 (Hz)', font=('Microsoft YaHei UI', 11),
                     text_color='#888888').grid(row=0, column=0, padx=4, sticky='w')
        sr_menu = ctk.CTkOptionMenu(grid, values=[str(s) for s in SAMPLE_RATES],
                                     variable=ctk.StringVar(value='48000'),
                                     font=('Microsoft YaHei UI', 12),
                                     fg_color='#1a1a3a', button_color='#1a1a3a',
                                     button_hover_color='#2a2a4a',
                                     dropdown_fg_color='#14142e',
                                     command=lambda v: sr_var.set(int(v)))
        sr_menu.grid(row=1, column=0, padx=4, pady=2)

        ctk.CTkLabel(grid, text='位深度', font=('Microsoft YaHei UI', 11),
                     text_color='#888888').grid(row=0, column=1, padx=4, sticky='w')
        bd_menu = ctk.CTkOptionMenu(grid, values=[str(b) for b in BIT_DEPTHS],
                                     variable=ctk.StringVar(value='24'),
                                     font=('Microsoft YaHei UI', 12),
                                     fg_color='#1a1a3a', button_color='#1a1a3a',
                                     button_hover_color='#2a2a4a',
                                     dropdown_fg_color='#14142e',
                                     command=lambda v: bd_var.set(int(v)))
        bd_menu.grid(row=1, column=1, padx=4, pady=2)

        ctk.CTkLabel(grid, text='通道', font=('Microsoft YaHei UI', 11),
                     text_color='#888888').grid(row=0, column=2, padx=4, sticky='w')
        ch_names = ['单声道', '立体声']
        ch_menu = ctk.CTkOptionMenu(grid, values=ch_names,
                                     variable=ctk.StringVar(value='立体声'),
                                     font=('Microsoft YaHei UI', 12),
                                     fg_color='#1a1a3a', button_color='#1a1a3a',
                                     button_hover_color='#2a2a4a',
                                     dropdown_fg_color='#14142e',
                                     command=lambda v: ch_var.set(1 if v == '单声道' else 2))
        ch_menu.grid(row=1, column=2, padx=4, pady=2)

        ctk.CTkLabel(form_frame, text='常用预设', font=('Microsoft YaHei UI', 11),
                     text_color='#888888', anchor='w').pack(fill='x', padx=16, pady=(12, 2))
        preset_frame = ctk.CTkFrame(form_frame, fg_color='transparent')
        preset_frame.pack(fill='x', padx=16)

        for label, sr, bd, ch in PRESETS:
            def make_cmd(sr=sr, bd=bd, ch=ch):
                return lambda: [sr_var.set(sr), bd_var.set(bd), ch_var.set(ch),
                                sr_menu.set(str(sr)), bd_menu.set(str(bd)),
                                ch_menu.set('单声道' if ch == 1 else '立体声')]
            ctk.CTkButton(
                preset_frame, text=f'{label} ({sr}/{bd}bit)',
                font=('Microsoft YaHei UI', 11), fg_color='#1a1a3a',
                hover_color='#2a2a4a', text_color='#999999',
                command=make_cmd()).pack(side='left', padx=2, pady=2)

        btn_row = ctk.CTkFrame(form_frame, fg_color='transparent')
        btn_row.pack(fill='x', padx=16, pady=(16, 12))
        ctk.CTkButton(btn_row, text='取消', font=('Microsoft YaHei UI', 12),
                      fg_color='#1a1a3a', hover_color='#2a2a4a',
                      text_color='#999999', command=dialog.destroy).pack(side='right', padx=4)

        def _apply():
            threading.Thread(target=lambda: (
                self.helper.send('set-device-format', id=device['id'],
                                 sample_rate=sr_var.get(),
                                 bit_depth=bd_var.get(),
                                 channels=ch_var.get()),
                self.after(200, self.refresh)
            ), daemon=True).start()
            dialog.destroy()

        ctk.CTkButton(btn_row, text='应用', font=('Microsoft YaHei UI', 12),
                      fg_color='#3b82f6', hover_color='#6090f0',
                      command=_apply).pack(side='right')

        # Fetch format in background
        def _fetch():
            try:
                fmt = self.helper.send('get-device-format', id=device['id'], timeout=2.0)
            except Exception:
                fmt = {}
            self.after(0, lambda: [
                sr_var.set(fmt.get('sampleRate', 48000)),
                bd_var.set(fmt.get('bitDepth', 24)),
                ch_var.set(fmt.get('channels', 2)),
                sr_menu.set(str(fmt.get('sampleRate', 48000))),
                bd_menu.set(str(fmt.get('bitDepth', 24))),
                ch_menu.set('单声道' if fmt.get('channels', 2) == 1 else '立体声'),
                loading_lbl.pack_forget(),
                form_frame.pack(fill='both', expand=True),
            ])
        threading.Thread(target=_fetch, daemon=True).start()


def _center_on_parent(dialog, parent):
    dialog.update_idletasks()
    pw = parent.winfo_toplevel()
    px = pw.winfo_x() + pw.winfo_width() // 2
    py = pw.winfo_y() + pw.winfo_height() // 2
    dw = dialog.winfo_reqwidth()
    dh = dialog.winfo_reqheight()
    x = max(0, min(px - dw // 2, pw.winfo_screenwidth() - dw))
    y = max(0, min(py - dh // 2, pw.winfo_screenheight() - dh - 40))
    dialog.geometry(f'+{x}+{y}')
