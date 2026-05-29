"""AudioCenter — Windows audio control panel (Python + customtkinter)."""
import sys
import os
import threading
import customtkinter as ctk
from audio import AudioHelper
from themecolors import C
import pystray
from PIL import Image

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

WIDTH, HEIGHT = 580, 700
MIN_W, MIN_H = 500, 580
SIDEBAR_W = 72

ICON_PATH = os.path.join(os.path.dirname(__file__), 'icon.ico')

TABS = [
    ('🎵', '音量', 'mixer'),
    ('🎧', '播放', 'playback'),
    ('🎤', '录制', 'recording'),
    ('🔧', 'Studio', 'studio'),
    ('💾', '配置', 'profiles'),
]


class AudioCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('AudioCenter - 阿云音频制作 微信：AyunAudio')
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.minsize(MIN_W, MIN_H)
        self.resizable(False, False)

        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - WIDTH) // 2)
        y = max(0, (sh - HEIGHT) // 2)
        self.geometry(f'{WIDTH}x{HEIGHT}+{x}+{y}')

        # Custom titlebar
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.after(10, self._set_taskbar_icon)

        self.helper = None
        self._active_tab = 0
        self._tray_icon = None

        # Build UI
        self._build_titlebar()
        self._build_body()
        self._build_loading()

        # Drag support
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

        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.after(100, self._init_helper)
        self._setup_tray()

    def _init_helper(self):
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
        self._loading_frame.destroy()
        self._build_content()
        self._switch_tab(0)

    def _show_init_error(self, msg):
        self._loading_label.configure(
            text=f'音频服务启动失败\n{msg}\n\n请以管理员身份运行此程序',
            text_color='#e74c3c')

    def _build_loading(self):
        self._loading_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self._loading_frame.pack(fill='both', expand=True)
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

        self.titlebar_label = ctk.CTkLabel(inner, text='AudioCenter - 阿云音频制作 微信：AyunAudio',
                                           font=('Segoe UI', 12, 'bold'),
                                           text_color=C['text_primary'])
        self.titlebar_label.pack(side='left')

        btn_style = {'width': 32, 'height': 22, 'fg_color': 'transparent',
                     'text_color': C['text_secondary'], 'font': ('Segoe UI', 12)}

        self.close_btn = ctk.CTkButton(inner, text='✕',
                                       command=self._on_close,
                                       hover_color='#cc3333', **btn_style)
        self.close_btn.pack(side='right')

        self.min_btn = ctk.CTkButton(inner, text='─', command=self._minimize,
                                     hover_color=C['btn_icon_hover'], **btn_style)
        self.min_btn.pack(side='right', padx=1)

    def _minimize(self):
        """Minimize to taskbar (works with overrideredirect)."""
        self.overrideredirect(False)
        self.iconify()
        self.after(100, self._restore_overrideredirect)

    def _restore_overrideredirect(self):
        if self.state() == 'normal':
            self.overrideredirect(True)
        else:
            self.after(100, self._restore_overrideredirect)

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, min(x, sw - 100))
        y = max(0, min(y, sh - 40))
        self.geometry(f'+{x}+{y}')

    def _set_taskbar_icon(self):
        import ctypes
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.overrideredirect(False)
        self.withdraw()
        self.after(50, self._restore_taskbar)

    def _restore_taskbar(self):
        self.overrideredirect(True)
        self.deiconify()

    def _on_close(self):
        """Minimize to tray instead of closing."""
        self.withdraw()

    def _quit_app(self):
        """Actually quit the application."""
        if self._tray_icon:
            try:
                self._tray_icon.visible = False
                self._tray_icon.stop()
            except Exception:
                pass
        if self.helper:
            self.helper.close()
        self.destroy()
        # Force exit to ensure temp dir cleanup
        import atexit, os
        atexit.register(lambda: None)
        os._exit(0)

    def _setup_tray(self):
        """Create system tray icon in a background thread."""
        def _create_icon():
            try:
                if os.path.exists(ICON_PATH):
                    img = Image.open(ICON_PATH)
                else:
                    img = Image.new('RGB', (64, 64), '#07C160')
            except Exception:
                img = Image.new('RGB', (64, 64), '#07C160')

            menu = pystray.Menu(
                pystray.MenuItem('显示窗口', lambda: self.after(0, self._show_window)),
                pystray.MenuItem('退出', lambda: self.after(0, self._quit_app)),
            )
            self._tray_icon = pystray.Icon(
                'AudioCenter', img, 'AudioCenter', menu)
            self._tray_icon.run()

        threading.Thread(target=_create_icon, daemon=True).start()

    def _show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    # ── sidebar ───────────────────────────────────────────────
    def _build_body(self):
        """Build sidebar + content area."""
        body = ctk.CTkFrame(self, fg_color='transparent')
        body.pack(fill='both', expand=True, side='top')

        # Sidebar
        self.sidebar = ctk.CTkFrame(body, width=SIDEBAR_W,
                                     fg_color=C['sidebar_bg'],
                                     corner_radius=0)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Content area
        self.content_area = ctk.CTkFrame(body, fg_color='transparent')
        self.content_area.pack(side='right', fill='both', expand=True)

        # Build sidebar buttons
        self._sidebar_buttons: list[ctk.CTkButton] = []
        self._sidebar_indicator = ctk.CTkFrame(
            self.sidebar, width=3, height=40,
            fg_color=C['accent'], corner_radius=0)

        for i, (icon, label, key) in enumerate(TABS):
            btn = ctk.CTkButton(
                self.sidebar, text=f'{icon}\n{label}',
                font=('Microsoft YaHei UI', 10),
                fg_color='transparent',
                text_color=C['text_dim'],
                hover_color=C['sidebar_hover'],
                corner_radius=8, width=60, height=56,
                command=lambda idx=i: self._switch_tab(idx),
            )
            btn.pack(pady=4, padx=6)
            self._sidebar_buttons.append(btn)

    def _switch_tab(self, idx):
        self._active_tab = idx
        # Update sidebar buttons
        for i, btn in enumerate(self._sidebar_buttons):
            if i == idx:
                btn.configure(fg_color=C['sidebar_active'],
                              text_color=C['accent'])
            else:
                btn.configure(fg_color='transparent',
                              text_color=C['text_dim'])

        # Move indicator
        self._sidebar_indicator.place(
            x=0, y=idx * 64 + 8 + 8)  # pady=4*2 + offset

        # Show content
        tab_keys = [t[2] for t in TABS]
        for key in tab_keys:
            frame = getattr(self, f'tab_{key}', None)
            if frame:
                frame.pack_forget()
        target = getattr(self, f'tab_{tab_keys[idx]}', None)
        if target:
            target.pack(fill='both', expand=True)

    # ── content ────────────────────────────────────────────────
    def _build_content(self):
        self.content_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        self.content_frame.pack(fill='both', expand=True)

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


if __name__ == '__main__':
    # Single instance check — prevent multiple windows
    import ctypes
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Global\\AudioCenter_AyunAudio')
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning('AudioCenter', '软件已在运行中，请勿重复打开。', parent=root)
        root.destroy()
        sys.exit(0)

    app = AudioCenter()
    app.mainloop()
