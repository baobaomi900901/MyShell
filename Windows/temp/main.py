#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw a Win32 rectangle overlay from an {x,y,w,h} argument.

Usage:
    python main.py "{x: 478, y: 380, w: 42, h: 28}"
    python main.py '{"X": 478, "Y": 380, "W": 42, "H": 28}'
"""

from __future__ import annotations

import ctypes
import json
import re
import sys
from ctypes import wintypes


def parse_args(raw: str) -> dict:
    """Parse JSON or JSON-like text such as "{x: 478, y: 380, w: 42, h: 28}"."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    text = raw.strip().replace("'", '"')
    text = re.sub(r'(?<!\w)([a-zA-Z_]\w*)(?=\s*:)', r'"\1"', text)
    return json.loads(text)


def _set_dpi_awareness() -> None:
    """Make coordinates match Win32 screen coordinates as closely as possible."""
    if sys.platform != "win32":
        return

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    try:
        mask = (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1
        per_monitor_v2 = ctypes.c_void_p((-4) & mask)
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
        if user32.SetProcessDpiAwarenessContext(per_monitor_v2):
            return
    except Exception:
        pass

    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        shcore.SetProcessDpiAwareness.argtypes = [ctypes.c_int]
        shcore.SetProcessDpiAwareness.restype = ctypes.c_long
        if int(shcore.SetProcessDpiAwareness(2)) == 0:
            return
    except Exception:
        pass

    try:
        user32.SetProcessDPIAware.argtypes = []
        user32.SetProcessDPIAware.restype = wintypes.BOOL
        user32.SetProcessDPIAware()
    except Exception:
        pass


def _rgb(r: int, g: int, b: int) -> int:
    return (int(b) & 0xFF) << 16 | (int(g) & 0xFF) << 8 | (int(r) & 0xFF)


def _hwnd_ptr(value):
    if not value:
        return ctypes.c_void_p(None)
    return ctypes.c_void_p(int(value))


def draw_rect(x: int, y: int, w: int, h: int, duration_ms: int = 5000) -> None:
    if sys.platform != "win32":
        raise RuntimeError("This script only supports Windows.")
    if w <= 0 or h <= 0:
        raise ValueError("w and h must be greater than 0.")

    _set_dpi_awareness()

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    LRESULT = getattr(wintypes, "LRESULT", ctypes.c_ssize_t)
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT,
        ctypes.c_void_p,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )

    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HANDLE),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [
            ("hdc", wintypes.HDC),
            ("fErase", wintypes.BOOL),
            ("rcPaint", wintypes.RECT),
            ("fRestore", wintypes.BOOL),
            ("fIncUpdate", wintypes.BOOL),
            ("rgbReserved", wintypes.BYTE * 32),
        ]

    WS_POPUP = 0x80000000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_NOACTIVATE = 0x08000000

    SW_SHOWNOACTIVATE = 4
    SWP_NOACTIVATE = 0x0010
    SWP_FRAMECHANGED = 0x0020
    SWP_SHOWWINDOW = 0x0040

    WM_DESTROY = 0x0002
    WM_PAINT = 0x000F
    WM_ERASEBKGND = 0x0014
    WM_CLOSE = 0x0010
    WM_TIMER = 0x0113

    LWA_COLORKEY = 0x1
    NULL_BRUSH = 5
    NULL_PEN = 8
    PS_SOLID = 0

    border_px = 4
    chroma = _rgb(1, 2, 3)
    purple = _rgb(160, 32, 240)
    class_name = "CoordinateCheck_Win32Overlay"
    title = "CoordinateCheckOverlay"

    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
    h_instance = kernel32.GetModuleHandleW(None)

    user32.DefWindowProcW.argtypes = [
        ctypes.c_void_p,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.DefWindowProcW.restype = LRESULT
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.HINSTANCE,
        ctypes.c_void_p,
    ]
    user32.CreateWindowExW.restype = ctypes.c_void_p
    user32.SetLayeredWindowAttributes.argtypes = [
        ctypes.c_void_p,
        wintypes.COLORREF,
        wintypes.BYTE,
        wintypes.DWORD,
    ]
    user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.SetTimer.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
    user32.DestroyWindow.argtypes = [ctypes.c_void_p]
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), ctypes.c_void_p, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]

    gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
    gdi32.CreatePen.restype = wintypes.HANDLE
    gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
    gdi32.CreateSolidBrush.restype = wintypes.HANDLE
    gdi32.GetStockObject.argtypes = [ctypes.c_int]
    gdi32.GetStockObject.restype = wintypes.HANDLE
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
    gdi32.SelectObject.restype = wintypes.HANDLE
    gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
    gdi32.Rectangle.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

    user32.BeginPaint.argtypes = [ctypes.c_void_p, ctypes.POINTER(PAINTSTRUCT)]
    user32.BeginPaint.restype = wintypes.HDC
    user32.EndPaint.argtypes = [ctypes.c_void_p, ctypes.POINTER(PAINTSTRUCT)]

    def wndproc(hwnd, msg, wparam, lparam):
        if msg == WM_ERASEBKGND:
            return 1
        if msg == WM_TIMER or msg == WM_CLOSE:
            user32.DestroyWindow(_hwnd_ptr(hwnd))
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        if msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(_hwnd_ptr(hwnd), ctypes.byref(ps))
            try:
                bg = gdi32.CreateSolidBrush(chroma)
                old_brush = gdi32.SelectObject(hdc, bg)
                old_pen = gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_PEN))
                try:
                    gdi32.Rectangle(hdc, 0, 0, int(w), int(h))
                finally:
                    gdi32.SelectObject(hdc, old_pen)
                    gdi32.SelectObject(hdc, old_brush)
                    gdi32.DeleteObject(bg)

                null_brush = gdi32.GetStockObject(NULL_BRUSH)
                pen = gdi32.CreatePen(PS_SOLID, border_px, purple)
                old_brush = gdi32.SelectObject(hdc, null_brush)
                old_pen = gdi32.SelectObject(hdc, pen)
                try:
                    gdi32.Rectangle(hdc, 0, 0, max(1, int(w)), max(1, int(h)))
                finally:
                    gdi32.SelectObject(hdc, old_pen)
                    gdi32.SelectObject(hdc, old_brush)
                    gdi32.DeleteObject(pen)
            finally:
                user32.EndPaint(_hwnd_ptr(hwnd), ctypes.byref(ps))
            return 0
        return user32.DefWindowProcW(_hwnd_ptr(hwnd), msg, wparam, lparam)

    wndproc_ref = WNDPROC(wndproc)
    wc = WNDCLASS()
    wc.lpfnWndProc = wndproc_ref
    wc.hInstance = h_instance
    wc.lpszClassName = class_name
    user32.RegisterClassW(ctypes.byref(wc))

    hwnd = user32.CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE,
        class_name,
        title,
        WS_POPUP,
        int(x),
        int(y),
        int(w),
        int(h),
        ctypes.c_void_p(None),
        ctypes.c_void_p(None),
        h_instance,
        ctypes.c_void_p(None),
    )
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    user32.SetLayeredWindowAttributes(_hwnd_ptr(hwnd), chroma, 0, LWA_COLORKEY)
    user32.SetWindowPos(
        _hwnd_ptr(hwnd),
        ctypes.c_void_p((-1) & ((1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1)),
        int(x),
        int(y),
        int(w),
        int(h),
        SWP_NOACTIVATE | SWP_SHOWWINDOW | SWP_FRAMECHANGED,
    )
    user32.ShowWindow(_hwnd_ptr(hwnd), SW_SHOWNOACTIVATE)
    user32.SetTimer(_hwnd_ptr(hwnd), 1, max(1, int(duration_ms)), None)

    msg = wintypes.MSG()
    while True:
        result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if result <= 0:
            break
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python main.py '{x: 478, y: 380, w: 42, h: 28}'")
        sys.exit(1)

    params = {str(k).lower(): v for k, v in parse_args(sys.argv[1]).items()}
    x = int(float(params.get("x", 0)))
    y = int(float(params.get("y", 0)))
    w = int(float(params.get("w", 100)))
    h = int(float(params.get("h", 50)))
    duration_ms = int(float(params.get("duration_ms", params.get("duration", 5000))))

    print(f"绘制 Win32 矩形: x={x}, y={y}, w={w}, h={h}, duration_ms={duration_ms}")
    draw_rect(x, y, w, h, duration_ms=duration_ms)


if __name__ == "__main__":
    main()
