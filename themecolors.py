"""Centralized theme colors for AudioCenter.

Usage:
    from themecolors import C, set_theme, apply_widget_theme
    fg = C['card_bg']
"""
import customtkinter as ctk

DARK = {
    'titlebar_bg':     '#0d0d1a',
    'tab_strip_bg':    '#12122a',
    'tab_active_bg':   '#1a1a3a',
    'tab_hover':       '#1a1a3a',
    'card_bg':         '#14142e',
    'card_border':     '#1e1e3a',
    'btn_bg':          '#1a1a3a',
    'btn_hover':       '#2a2a4a',
    'btn_icon_hover':  '#222244',
    'slider_bg':       '#1a1a3a',
    'dropdown_bg':     '#14142e',
    'dropdown_hover':  '#222244',
    'scrollbar':       '#222244',
    'text_primary':    '#cccccc',
    'text_secondary':  '#999999',
    'text_dim':        '#666666',
    'text_muted':      '#555555',
    'accent':          '#3b82f6',
    'danger':          '#dc2626',
    'danger_hover':    '#991b1b',
    'warning':         '#f59e0b',
    'success':         '#22c55e',
    'offline':         '#6b7280',
}

LIGHT = {
    'titlebar_bg':     '#e0e0e0',
    'tab_strip_bg':    '#d8d8e8',
    'tab_active_bg':   '#c8c8e0',
    'tab_hover':       '#d0d0e0',
    'card_bg':         '#f0f0f8',
    'card_border':     '#c0c0d0',
    'btn_bg':          '#dcdce8',
    'btn_hover':       '#c8c8d8',
    'btn_icon_hover':  '#d0d0e0',
    'slider_bg':       '#dcdce8',
    'dropdown_bg':     '#f0f0f8',
    'dropdown_hover':  '#d0d0e0',
    'scrollbar':       '#c0c0d0',
    'text_primary':    '#222222',
    'text_secondary':  '#555555',
    'text_dim':        '#888888',
    'text_muted':      '#666666',
    'accent':          '#3b82f6',
    'danger':          '#dc2626',
    'danger_hover':    '#991b1b',
    'warning':         '#d97706',
    'success':         '#16a34a',
    'offline':         '#9ca3af',
}

# Dark hex → light key name mapping
_DARK_HEX_TO_KEY = {
    '#14142e': 'card_bg',    '#1a1a3a': 'btn_bg',
    '#1e1e3a': 'card_border', '#0d0d1a': 'titlebar_bg',
    '#12122a': 'tab_strip_bg', '#222244': 'btn_icon_hover',
    '#2a2a4a': 'btn_hover',   '#333355': 'btn_hover',
    '#cccccc': 'text_primary', '#999999': 'text_secondary',
    '#888888': 'text_dim',    '#666666': 'text_dim',
    '#555555': 'text_muted',  '#aaaaaa': 'text_secondary',
    '#3b82f6': 'accent',      '#dc2626': 'danger',
    '#991b1b': 'danger_hover', '#f59e0b': 'warning',
    '#22c55e': 'success',     '#16a34a': 'success',
    '#6b7280': 'offline',     '#9ca3af': 'offline',
    '#dcdce8': 'btn_bg',      '#c0c0d0': 'card_border',
    '#f0f0f8': 'card_bg',     '#c8c8d8': 'btn_hover',
    '#d0d0e0': 'tab_hover',   '#222222': 'text_primary',
    '#d97706': 'warning',
}

C = DARK


def set_theme(light: bool = False):
    global C
    src = LIGHT if light else DARK
    C.clear()
    C.update(src)


def _remap_color(val, colors) -> str | None:
    """Map any color value (str or tuple) to the current theme equivalent."""
    if isinstance(val, str) and val.lower() in _DARK_HEX_TO_KEY:
        return colors[_DARK_HEX_TO_KEY[val.lower()]]
    if isinstance(val, (tuple, list)) and len(val) == 2:
        # (dark, light) tuple — pick based on whether colors is DARK or LIGHT
        if colors.get('titlebar_bg') == DARK['titlebar_bg']:
            return val[0]  # dark mode → first element
        else:
            return val[1]  # light mode → second element
    return None


def apply_widget_theme(widget, colors):
    """Walk the widget tree and swap known hex colors to their theme equivalents.
    Also forces text_color on labels/buttons for proper contrast."""
    is_light = colors.get('titlebar_bg') != DARK['titlebar_bg']

    if isinstance(widget, ctk.CTkFrame):
        for attr in ('fg_color', 'border_color', 'scrollbar_button_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass

    elif isinstance(widget, (ctk.CTkButton, ctk.CTkEntry)):
        for attr in ('fg_color', 'hover_color', 'border_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass
        # Force button text: if text_color is not a special accent, set to primary
        try:
            tc = widget.cget('text_color')
            if isinstance(tc, str) and tc.lower() in ('#3b82f6', '#f59e0b', '#dc2626', '#22c55e', '#16a34a',
                                                       '#d97706', '#991b1b'):
                pass  # keep accent colors
            elif isinstance(tc, tuple):
                pass  # already tuple means ctk is managing it
            else:
                widget.configure(text_color=colors['text_primary'] if not is_light else colors['text_primary'])
        except Exception:
            pass

    elif isinstance(widget, ctk.CTkLabel):
        try:
            # Always update label text color for contrast
            tc = widget.cget('text_color')
            if isinstance(tc, str) and tc.lower() in ('#3b82f6', '#f59e0b', '#dc2626', '#22c55e', '#16a34a',
                                                       '#d97706', '#991b1b'):
                pass  # keep accent
            elif isinstance(tc, tuple):
                pass
            else:
                nv = _remap_color(tc, colors)
                widget.configure(text_color=nv if nv else colors['text_primary'])
        except Exception:
            pass

    elif isinstance(widget, ctk.CTkOptionMenu):
        for attr in ('fg_color', 'button_color', 'dropdown_fg_color',
                     'button_hover_color', 'dropdown_hover_color', 'text_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass

    elif isinstance(widget, ctk.CTkSlider):
        for attr in ('fg_color', 'progress_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass

    elif isinstance(widget, ctk.CTkTextbox):
        for attr in ('fg_color', 'text_color', 'border_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass

    elif isinstance(widget, ctk.CTkScrollableFrame):
        for attr in ('fg_color', 'scrollbar_button_color', 'scrollbar_button_hover_color'):
            try:
                v = widget.cget(attr)
                nv = _remap_color(v, colors)
                if nv:
                    widget.configure(**{attr: nv})
            except Exception:
                pass

    for child in widget.winfo_children():
        apply_widget_theme(child, colors)
