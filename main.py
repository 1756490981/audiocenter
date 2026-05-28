"""AudioCenter — Windows audio control panel (Python + customtkinter)."""
import sys
import os
import customtkinter as ctk
from audio import AudioHelper
from themecolors import C

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

WIDTH, HEIGHT = 540, 640
MIN_W, MIN_H = 460, 520

ICON_PATH = os.path.join(os.path.dirname(__file__), 'icon.ico')


class AudioCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('AudioCenter - 阿云音频制作')
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.minsize(MIN_W, MIN_H)
        self.resizable(False, False)

        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)

        # Center on screen (within bounds)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - WIDTH) // 2)
        y = max(0, (sh - HEIGHT) // 2)
        self.geometry(f'{WIDTH}x{HEIGHT}+{x}+{y}')

        # Remove native titlebar (we draw our own)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.after(200, lambda: self.attributes('-topmost', False))

        # Show in taskbar despite overrideredirect
        self.after(10, self._set_taskbar_icon)

        # Placeholder — real helper created after window is mapped
        self.helper = None

        # Build UI
        self._build_titlebar()
        self._build_tabs()
        self._build_loading()

        # Drag support for custom titlebar — bind to titlebar and all non-button children
        self._drag_x = 0
        self._drag_y = 0
        self.titlebar.bind('<Button-1>', self._drag_start)
        self.titlebar.bind('<B1-Motion>', self._drag_move)
        inner = self._titlebar_inner
        inner.bind('<Button-1>', self._drag_start)
        inner.bind('<B1-Motion>', self._drag_move)
        for lbl in [self.titlebar_icon, self.titlebar_label]:
            lbl.bind('<Button-1>', self._drag_start)
            lbl.bind('<B1-Motion>', self._drag_move)

        # Handle close
        self.protocol('WM_DELETE_WINDOW', self._on_close)

        # Start AudioHelper in background (UAC prompt will appear)
        self.after(100, self._init_helper)

    def _init_helper(self):
        """Start AudioHelper in background (may trigger UAC prompt)."""
        import threading
        def _start():
            try:
                self.helper = AudioHelper()
            except Exception as e:
                self.after(0, self._show_init_error, str(e))
                return
            self.after(0, self._on_helper_ready)
        threading.Thread(target=_start, daemon=True).start()

    def _on_helper_ready(self):
        """Called when AudioHelper is ready — replace loading with content."""
        self._loading_frame.destroy()
        self._build_content()

    def _show_init_error(self, msg):
        self._loading_label.configure(
            text=f'音频服务启动失败\n{msg}\n\n请以管理员身份运行此程序',
            text_color='#dc2626')

    def _build_loading(self):
        """Show loading state while AudioHelper starts."""
        self._loading_frame = ctk.CTkFrame(self, fg_color='transparent')
        self._loading_frame.pack(fill='both', expand=True, side='top')
        self._loading_label = ctk.CTkLabel(
            self._loading_frame,
            text='正在启动音频服务...\n\n如弹出用户账户控制窗口，请点击"是"',
            font=('Microsoft YaHei UI', 14),
            text_color='#888888')
        self._loading_label.place(relx=0.5, rely=0.5, anchor='center')

    # ── titlebar ──────────────────────────────────────────────
    def _build_titlebar(self):
        self.titlebar = ctk.CTkFrame(self, height=32,
                                     fg_color=C['titlebar_bg'],
                                     corner_radius=0)
        self.titlebar.pack(fill='x', side='top')
        self.titlebar.pack_propagate(False)

        inner = ctk.CTkFrame(self.titlebar, fg_color='transparent')
        inner.pack(fill='both', expand=True, padx=8)
        self._titlebar_inner = inner

        self.titlebar_icon = ctk.CTkLabel(inner, text='🎵', font=('Segoe UI', 15))
        self.titlebar_icon.pack(side='left', padx=(4, 2))

        self.titlebar_label = ctk.CTkLabel(inner, text='AudioCenter - 阿云音频制作',
                                           font=('Segoe UI', 12, 'bold'),
                                           text_color=C['text_primary'])
        self.titlebar_label.pack(side='left')

        btn_style = {'width': 32, 'height': 22, 'fg_color': 'transparent',
                     'text_color': C['text_secondary'], 'font': ('Segoe UI', 12)}

        self.close_btn = ctk.CTkButton(inner, text='✕',
                                       command=self._on_close,
                                       hover_color='#cc3333', **btn_style)
        self.close_btn.pack(side='right')

        self.min_btn = ctk.CTkButton(inner, text='─', command=self.iconify,
                                     hover_color=C['btn_icon_hover'], **btn_style)
        self.min_btn.pack(side='right', padx=1)

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        # Keep window on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, min(x, sw - 100))
        y = max(0, min(y, sh - 40))
        self.geometry(f'+{x}+{y}')

    def _set_taskbar_icon(self):
        """Force overrideredirect window to appear in the taskbar."""
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        # Re-withdraw/deiconify to make taskbar pick up the new style
        self.withdraw()
        self.after(10, self.deiconify)

    def _on_close(self):
        if self.helper:
            self.helper.close()
        self.destroy()

    # ── tabs ───────────────────────────────────────────────────
    def _build_tabs(self):
        self.tab_frame = ctk.CTkFrame(self, height=34,
                                      fg_color=C['tab_strip_bg'],
                                      corner_radius=0)
        self.tab_frame.pack(fill='x', side='top')
        self.tab_frame.pack_propagate(False)

        btn_font = ('Segoe UI', 13)
        self._tab_buttons: list[ctk.CTkButton] = []
        self._active_tab = 0

        tabs = [
            ('🎵 音量混合器', 'mixer'),
            ('🎧 播放设备', 'playback'),
            ('🎤 录制设备', 'recording'),
            ('💾 高级功能', 'profiles'),
            ('🔧 Studio One', 'studio'),
        ]

        tab_btn_w = (WIDTH - 5) // 5
        for i, (label, key) in enumerate(tabs):
            btn = ctk.CTkButton(
                self.tab_frame, text=label, font=btn_font,
                fg_color='transparent', text_color=C['text_secondary'],
                hover_color=C['tab_hover'], corner_radius=0, width=tab_btn_w,
                command=lambda k=key, idx=i: self._switch_tab(idx),
            )
            btn.pack(side='left', fill='y', padx=0)
            self._tab_buttons.append(btn)

        self._tab_indicator = ctk.CTkFrame(
            self.tab_frame, height=2, width=120,
            fg_color=C['accent'], corner_radius=0)
        self._tab_indicator.place(x=0, y=32)

    def _switch_tab(self, idx):
        self._active_tab = idx
        for i, btn in enumerate(self._tab_buttons):
            btn.configure(
                text_color=C['accent'] if i == idx else C['text_secondary'],
                fg_color=C['tab_active_bg'] if i == idx else 'transparent',
            )
        # Move indicator
        tw = (WIDTH - 5) // 5
        self._tab_indicator.configure(width=tw)
        self._tab_indicator.place(x=idx * tw, y=32)

        # Show content
        tab_names = ['mixer', 'playback', 'recording', 'profiles', 'studio']
        for name in tab_names:
            frame = getattr(self, f'tab_{name}', None)
            if frame:
                frame.pack_forget()
        getattr(self, f'tab_{tab_names[idx]}').pack(fill='both', expand=True)

    # ── content ────────────────────────────────────────────────
    def _build_content(self):
        self.content_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.content_frame.pack(fill='both', expand=True, side='top')

        from tabs.mixer import VolumeMixerTab
        from tabs.playback import PlaybackDeviceTab
        from tabs.recording import RecordingDeviceTab
        from tabs.profiles import ProfileManagerTab
        from tabs.studio import StudioOneTab

        self.tab_mixer = VolumeMixerTab(self.content_frame, self.helper)
        self.tab_playback = PlaybackDeviceTab(self.content_frame, self.helper)
        self.tab_recording = RecordingDeviceTab(self.content_frame, self.helper)
        self.tab_profiles = ProfileManagerTab(self.content_frame, self.helper)
        self.tab_studio = StudioOneTab(self.content_frame, self.helper)

        self.tab_mixer.pack(fill='both', expand=True)
        self._tab_buttons[0].configure(text_color=C['accent'], fg_color=C['tab_active_bg'])


if __name__ == '__main__':
    from license import verify_license
    ok, machine_id, err = verify_license()
    if not ok:
        # Show activation dialog
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        if os.path.exists(ICON_PATH):
            try:
                root.iconbitmap(ICON_PATH)
            except Exception:
                pass
        messagebox.showerror(
            'AudioCenter - 未授权',
            f'本软件需要授权才能使用。\n\n'
            f'机器码：{machine_id}\n\n'
            f'请联系开发者获取授权码：\n'
            f'微信：AyunAudio\n\n'
            f'（将授权码保存为 license.dat 放到程序目录即可）',
            parent=root
        )
        root.destroy()
        sys.exit(0)

    app = AudioCenter()
    app.mainloop()
