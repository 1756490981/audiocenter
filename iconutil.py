"""Extract file icons from .exe/.dll on Windows using SHGetFileInfoW + GDI."""
import ctypes
from ctypes import wintypes
from PIL import Image
import customtkinter as ctk

# Cache: file_path -> CTkImage (cleared on _render_session for new sessions only)
_icon_cache: dict[str, ctk.CTkImage] = {}

SHGFI_ICON = 0x100
SHGFI_LARGEICON = 0x0
SHGFI_SMALLICON = 0x1

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def get_icon_ctk(file_path: str | None, size: int = 24) -> ctk.CTkImage | None:
    """Return a CTkImage for the given file's icon, or None on failure."""
    if not file_path:
        return None
    if file_path in _icon_cache:
        return _icon_cache[file_path]

    pil_img = _extract_icon_pil(file_path, size)
    if pil_img is None:
        _icon_cache[file_path] = None  # don't retry failures
        return None

    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    _icon_cache[file_path] = ctk_img
    return ctk_img


def _extract_icon_pil(file_path: str, size: int) -> Image.Image | None:
    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    info = SHFILEINFOW()
    ret = shell32.SHGetFileInfoW(
        file_path, 0, ctypes.byref(info), ctypes.sizeof(info),
        SHGFI_ICON | SHGFI_LARGEICON)
    if ret == 0 or not info.hIcon:
        return None

    hicon = info.hIcon

    # Draw icon onto a bitmap
    hdc = user32.GetDC(0)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, size, size)
    old_bmp = gdi32.SelectObject(memdc, bmp)

    # Fill with transparent-friendly dark background (#14142e in BGR)
    brush = gdi32.CreateSolidBrush(0x2E1414)
    rect = wintypes.RECT(0, 0, size, size)
    user32.FillRect(memdc, ctypes.byref(rect), brush)
    gdi32.DeleteObject(brush)

    user32.DrawIconEx(memdc, 0, 0, hicon, size, size, 0, 0, 0x0003)  # DI_NORMAL

    # GetDIBits
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = size
    bmi.biHeight = -size  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = (ctypes.c_ubyte * (size * size * 4))()
    gdi32.GetDIBits(memdc, bmp, 0, size, buf, ctypes.byref(bmi), 0)

    # Cleanup
    gdi32.SelectObject(memdc, old_bmp)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(0, hdc)
    user32.DestroyIcon(hicon)

    # BGRA → RGBA
    return Image.frombytes('RGBA', (size, size), bytes(buf), 'raw', 'BGRA', 0, 1)
