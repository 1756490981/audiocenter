"""Profile manager tab — save/load/delete/export/import audio profiles."""
import os
import json
import customtkinter as ctk
import threading
from tkinter import filedialog
from themecolors import C

# Studio One ASIO config companion files
_ASIO_PROFILE_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AudioCenter', 'profiles')


def _asio_save(name):
    """Save current Studio One ASIO config alongside the profile."""
    try:
        from tabs.studio import read_audio_engine, _load_selected_driver
        cfg = read_audio_engine()
        if not cfg:
            return
        os.makedirs(_ASIO_PROFILE_DIR, exist_ok=True)
        data = {
            'masterDevice': cfg.get('masterDevice', ''),
            'sampleRate': cfg.get('sampleRate', '48000'),
            'deviceBlockSize': cfg.get('deviceBlockSize', '128'),
            'selectedDriverClsid': _load_selected_driver(),
            'floatType': cfg.get('floatType', '0'),
            'dropOutProtectionLevel': cfg.get('dropOutProtectionLevel', '0'),
            'suspendInBackground': cfg.get('suspendInBackground', '0'),
            'silencePolicy': cfg.get('silencePolicy', '1'),
            'useEfficiencyCores': cfg.get('useEfficiencyCores', '0'),
        }
        path = os.path.join(_ASIO_PROFILE_DIR, f'{name}.asio')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _asio_load(name):
    """Restore Studio One ASIO config from companion file."""
    try:
        from tabs.studio import write_audio_engine, _save_selected_driver
        path = os.path.join(_ASIO_PROFILE_DIR, f'{name}.asio')
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        master = data.get('masterDevice', '')
        if not master:
            return
        _save_selected_driver(data.get('selectedDriverClsid', ''))
        write_audio_engine(
            master_device=master,
            sample_rate=data.get('sampleRate', '48000'),
            block_size=data.get('deviceBlockSize', '128'),
            floatType=data.get('floatType', '0'),
            dropOutProtectionLevel=data.get('dropOutProtectionLevel', '0'),
            suspendInBackground=data.get('suspendInBackground', '0'),
            silencePolicy=data.get('silencePolicy', '1'),
            useEfficiencyCores=data.get('useEfficiencyCores', '0'),
        )
    except Exception:
        pass


class ProfileManagerTab(ctk.CTkFrame):
    def __init__(self, parent, helper):
        super().__init__(parent, fg_color='transparent')
        self.helper = helper
        self._profiles: list[dict] = []
        self._toast: ctk.CTkLabel | None = None
        self._themed_widgets: list = []  # widgets to update on theme change

        # ── header ──
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=12, pady=(8, 2))
        ctk.CTkLabel(header, text='此软件由阿云音频修改制作 微信：AyunAudio',
                     font=('Microsoft YaHei UI', 11),
                     text_color=C['text_muted']).pack(side='left')
        ctk.CTkButton(header, text='↻', width=28, height=28,
                      fg_color='transparent', hover_color=C['btn_icon_hover'],
                      font=('Segoe UI', 16), text_color=C['text_dim'],
                      command=self.refresh).pack(side='right')

        # ── quick actions ──
        quick_frame = ctk.CTkFrame(self, fg_color=C['card_bg'], corner_radius=10,
                                   border_width=1, border_color=C['card_border'])
        quick_frame.pack(fill='x', padx=12, pady=(2, 4))
        self._themed_widgets.append(('card', quick_frame))

        ctk.CTkLabel(quick_frame, text='快捷操作', font=('Microsoft YaHei UI', 12),
                     text_color=C['text_secondary']).pack(anchor='w', padx=12, pady=(6, 2))

        ctk.CTkButton(
            quick_frame, text='🔊  所有音量调到 100',
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], hover_color=C['btn_hover'],
            text_color=C['text_primary'], anchor='w',
            command=self._max_all
        ).pack(fill='x', padx=12, pady=(2, 6))

        # ── save section ──
        save_frame = ctk.CTkFrame(self, fg_color=C['card_bg'], corner_radius=10,
                                  border_width=1, border_color=C['card_border'])
        save_frame.pack(fill='x', padx=12, pady=(0, 4))
        self._themed_widgets.append(('card', save_frame))

        ctk.CTkLabel(save_frame, text='保存当前设置', font=('Microsoft YaHei UI', 12),
                     text_color=C['text_secondary']).pack(anchor='w', padx=12, pady=(6, 2))

        row = ctk.CTkFrame(save_frame, fg_color='transparent')
        row.pack(fill='x', padx=12, pady=(2, 6))

        self._save_entry = ctk.CTkEntry(
            row, placeholder_text='输入配置名称...',
            font=('Microsoft YaHei UI', 12),
            fg_color=C['btn_bg'], border_color=C['card_border'],
            text_color=C['text_primary'])
        self._save_entry.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self._save_entry.bind('<Return>', lambda e: self._save())

        self._save_btn = ctk.CTkButton(
            row, text='💾  保存', font=('Microsoft YaHei UI', 12),
            fg_color=C['accent'], hover_color='#6090f0',
            width=80, command=self._save)
        self._save_btn.pack(side='right')

        # ── profile list (scrollable) ──
        self._list_header = ctk.CTkLabel(
            self, text='暂无保存的配置', font=('Microsoft YaHei UI', 12),
            text_color=C['text_muted'], anchor='w')
        self._list_header.pack(fill='x', padx=12, pady=(2, 1))

        self._list_area = ctk.CTkScrollableFrame(
            self, fg_color='transparent', scrollbar_button_color=C['scrollbar'],
            scrollbar_button_hover_color=C['btn_hover'])
        self._list_area.pack(fill='both', expand=True, padx=12, pady=2)

        # ── import button ──
        self._import_btn = ctk.CTkButton(
            self, text='📂  点击选择配置文件导入',
            font=('Microsoft YaHei UI', 12),
            fg_color='transparent', hover_color=C['tab_hover'],
            text_color=C['text_dim'], border_width=2, border_color=C['card_border'],
            command=self._import)
        self._import_btn.pack(fill='x', padx=12, pady=(2, 6))

        self.refresh()

    # ── toast ──
    def _show_toast(self, text, is_error=False):
        if self._toast:
            self._toast.destroy()
        root = self.winfo_toplevel()
        self._toast = ctk.CTkLabel(
            root, text=text, font=('Microsoft YaHei UI', 13),
            fg_color=C['danger'] if is_error else C['success'],
            text_color='#ffffff', corner_radius=8,
            width=200, height=32)
        self._toast.place(relx=0.5, rely=0.92, anchor='s')
        self._toast.lift()
        self.after(3000, self._hide_toast)

    def _hide_toast(self):
        if self._toast:
            self._toast.destroy()
            self._toast = None

    # ── refresh ──
    def refresh(self):
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        try:
            r = self.helper.send('list-profiles', timeout=2.0)
            profiles = r.get('profiles', [])
        except Exception:
            return
        self.after(0, self._apply_refresh, profiles)

    def _apply_refresh(self, profiles):
        self._profiles = profiles
        self._render_list()

    def _render_list(self):
        for child in self._list_area.winfo_children():
            child.destroy()

        if not self._profiles:
            self._list_header.configure(text='暂无保存的配置')
        else:
            self._list_header.configure(text=f'已保存的配置 ({len(self._profiles)})')

        for p in self._profiles:
            self._render_profile(p)

    def _render_profile(self, p: dict):
        name = p.get('name', '')
        file_name = p.get('fileName', '')
        created = p.get('createdAt', '')
        # Format date
        try:
            import datetime
            dt = datetime.datetime.fromisoformat(created.replace('Z', '+00:00'))
            date_str = dt.strftime('%m月%d日 %H:%M')
        except Exception:
            date_str = created

        frame = ctk.CTkFrame(self._list_area, fg_color=C['card_bg'],
                              corner_radius=8, border_width=1,
                              border_color=C['card_border'])
        frame.pack(fill='x', pady=2)

        info = ctk.CTkFrame(frame, fg_color='transparent')
        info.pack(side='left', fill='x', expand=True, padx=10, pady=8)

        ctk.CTkLabel(info, text=name, font=('Microsoft YaHei UI', 13),
                     text_color=C['text_primary'], anchor='w').pack(fill='x')
        ctk.CTkLabel(info, text=date_str, font=('Microsoft YaHei UI', 11),
                     text_color=C['text_muted'], anchor='w').pack(fill='x')

        btns = ctk.CTkFrame(frame, fg_color='transparent')
        btns.pack(side='right', padx=6, pady=8)

        ctk.CTkButton(btns, text='恢复', font=('Microsoft YaHei UI', 11),
                      fg_color='transparent', hover_color=C['tab_hover'],
                      text_color=C['accent'], width=44, height=24,
                      command=lambda fn=file_name: self._load(fn)).pack(side='left', padx=1)

        ctk.CTkButton(btns, text='导出', font=('Microsoft YaHei UI', 11),
                      fg_color='transparent', hover_color=C['tab_hover'],
                      text_color=C['text_dim'], width=44, height=24,
                      command=lambda fn=file_name: self._export(fn)).pack(side='left', padx=1)

        ctk.CTkButton(btns, text='🗑', font=('Segoe UI', 12),
                      fg_color='transparent', hover_color='#331111',
                      text_color=C['text_dim'], width=28, height=24,
                      command=lambda fn=file_name: self._delete(fn)).pack(side='left', padx=1)

    # ── actions ──
    def _save(self):
        name = self._save_entry.get().strip()
        if not name:
            return
        self._save_btn.configure(text='保存中...', state='disabled')
        def _run():
            try:
                r = self.helper.send('save-profile', name=name, timeout=3.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                else:
                    _asio_save(name)
                    self.after(0, self._show_toast, f'已保存: {name}', False)
                    self.after(0, lambda: self._save_entry.delete(0, 'end'))
                    self.after(0, self.refresh)
            except Exception as e:
                self.after(0, self._show_toast, f'保存失败: {e}', True)
            self.after(0, lambda: self._save_btn.configure(text='💾  保存', state='normal'))
        threading.Thread(target=_run, daemon=True).start()

    def _load(self, file_name):
        def _run():
            try:
                r = self.helper.send('load-profile', name=file_name, timeout=5.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                    return
                _asio_load(file_name)
                errors = r.get('errors', [])
                if errors:
                    self.after(0, self._show_toast, f'已恢复（部分失败: {", ".join(errors)}）', True)
                else:
                    self.after(0, self._show_toast, '已恢复（含Studio One配置）', False)
            except Exception as e:
                self.after(0, self._show_toast, f'恢复失败: {e}', True)
        threading.Thread(target=_run, daemon=True).start()

    def _delete(self, file_name):
        def _run():
            try:
                r = self.helper.send('delete-profile', name=file_name, timeout=3.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                else:
                    self.after(0, self._show_toast, '已删除', False)
                    self.after(0, self.refresh)
            except Exception as e:
                self.after(0, self._show_toast, f'删除失败: {e}', True)
        threading.Thread(target=_run, daemon=True).start()

    def _export(self, file_name):
        dest = filedialog.asksaveasfilename(
            defaultextension='.json',
            initialfile=file_name,
            filetypes=[('JSON 文件', '*.json')],
            title='导出配置文件')
        if not dest:
            return
        def _run():
            try:
                r = self.helper.send('export-profile', name=file_name, dest_path=dest, timeout=5.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                else:
                    self.after(0, self._show_toast, '已导出', False)
            except Exception as e:
                self.after(0, self._show_toast, f'导出失败: {e}', True)
        threading.Thread(target=_run, daemon=True).start()

    def _import(self):
        source = filedialog.askopenfilename(
            filetypes=[('JSON 文件', '*.json')],
            title='导入配置文件')
        if not source:
            return
        def _run():
            try:
                r = self.helper.send('import-profile', source_path=source, timeout=5.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                else:
                    self.after(0, self._show_toast, f'已导入: {r.get("name", "")}', False)
                    self.after(0, self.refresh)
            except Exception as e:
                self.after(0, self._show_toast, f'导入失败: {e}', True)
        threading.Thread(target=_run, daemon=True).start()

    def _max_all(self):
        def _run():
            try:
                r = self.helper.send('max-all-volumes', timeout=3.0)
                if r.get('error'):
                    self.after(0, self._show_toast, r['error'], True)
                else:
                    self.after(0, self._show_toast, '所有音量已调到 100', False)
            except Exception as e:
                self.after(0, self._show_toast, f'操作失败: {e}', True)
        threading.Thread(target=_run, daemon=True).start()

    def apply_theme(self, colors):
        """Update colors when theme toggles."""
        self._list_header.configure(text_color=colors['text_muted'])
        self._save_entry.configure(fg_color=colors['btn_bg'], border_color=colors['card_border'],
                                   text_color=colors['text_primary'])
        self._import_btn.configure(hover_color=colors['tab_hover'], text_color=colors['text_dim'],
                                   border_color=colors['card_border'])
        for t, w in self._themed_widgets:
            if t == 'card':
                w.configure(fg_color=colors['card_bg'], border_color=colors['card_border'])
        # Rebuild profile list
        self._render_list()
