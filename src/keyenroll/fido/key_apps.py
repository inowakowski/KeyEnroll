"""Other programs that talk to security keys and get in the way of an enrollment.

Yubico Authenticator polls the connected keys. While it runs, the key answers
another program between the steps of an enrollment: requests wait for a busy
channel, and a factory reset right after the key is re-inserted can be lost.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

AUTHENTICATOR = "Yubico Authenticator"
MANAGER = "YubiKey Manager"
YUBIENROLL = "YubiEnroll"

# Executable name (lower case, without .exe) -> program. The names marked
# True are generic and only count when the path names Yubico.
_KNOWN: dict[str, tuple[str, bool]] = {
    "authenticator": (AUTHENTICATOR, True),  # Yubico Authenticator 6 and 7
    "authenticator-helper": (AUTHENTICATOR, True),
    "yubico authenticator": (AUTHENTICATOR, False),  # macOS app bundle
    "yubioath-desktop": (AUTHENTICATOR, False),  # Yubico Authenticator 5
    "ykman-gui": (MANAGER, False),
    "ykman": (MANAGER, False),
    "yubienroll": (YUBIENROLL, False),
}


@dataclass(frozen=True)
class Process:
    pid: int
    name: str  # executable file name
    path: str = ""  # full path when it could be read


@dataclass
class KeyApp:
    """A program found running, with all of its processes."""

    name: str
    pids: list[int]


def _program(proc: Process) -> str | None:
    base = proc.name.lower()
    if base.endswith(".exe"):
        base = base[:-4]
    known = _KNOWN.get(base)
    if known is None:
        return None
    program, generic = known
    if generic and "yubico" not in proc.path.lower():
        return None
    return program


def find(processes: list[Process] | None = None) -> list[KeyApp]:
    """Programs from the list above that are running now, in a stable order."""
    if processes is None:
        processes = running()
    found: dict[str, KeyApp] = {}
    own = os.getpid()
    for proc in processes:
        program = _program(proc)
        if program and proc.pid != own:
            found.setdefault(program, KeyApp(program, [])).pids.append(proc.pid)
    return [found[name] for name in (AUTHENTICATOR, MANAGER, YUBIENROLL) if name in found]


def running() -> list[Process]:
    try:
        return _running_windows() if sys.platform == "win32" else _running_posix()
    except Exception:
        logger.debug("Listing processes failed", exc_info=True)
        return []


def close(apps: list[KeyApp], timeout: float = 5.0) -> list[KeyApp]:
    """Ends the processes of the programs; returns those still running."""
    pids = {pid for app in apps for pid in app.pids}
    for pid in pids:
        try:
            _terminate(pid)
        except Exception:
            logger.debug("Ending process %s failed", pid, exc_info=True)
    deadline = time.monotonic() + timeout
    while True:
        left = [app for app in find() if set(app.pids) & pids]
        if not left or time.monotonic() >= deadline:
            return left
        time.sleep(0.2)


# -- Windows ---------------------------------------------------------------

_TH32CS_SNAPPROCESS = 0x00000002
_PROCESS_TERMINATE = 0x0001
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _kernel32():
    import ctypes
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    return k


def _running_windows() -> list[Process]:
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    k = _kernel32()
    k.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    snapshot = k.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if not snapshot or snapshot == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    out = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = k.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            name = entry.szExeFile
            path = ""
            base = name.lower().removesuffix(".exe")
            if base in _KNOWN:  # only these need their path
                path = _image_path(k, entry.th32ProcessID)
            out.append(Process(entry.th32ProcessID, name, path))
            ok = k.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        k.CloseHandle(snapshot)
    return out


def _image_path(k, pid: int) -> str:
    import ctypes
    from ctypes import wintypes

    handle = k.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        if k.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value
        return ""
    finally:
        k.CloseHandle(handle)


def _terminate(pid: int) -> None:
    if sys.platform != "win32":
        os.kill(pid, signal.SIGTERM)
        return
    import ctypes

    k = _kernel32()
    handle = k.OpenProcess(_PROCESS_TERMINATE, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")
    try:
        if not k.TerminateProcess(handle, 1):
            raise OSError(ctypes.get_last_error(), "TerminateProcess failed")
    finally:
        k.CloseHandle(handle)


# -- macOS and Linux -------------------------------------------------------


def _running_posix() -> list[Process]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,args="], capture_output=True, text=True, timeout=10
    )
    out = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            command = parts[1]
            out.append(Process(int(parts[0]), _name_in(command), command))
    return out


def _name_in(command: str) -> str:
    """The executable name out of a command line. Paths may contain spaces
    (macOS app bundles do), so the known names are looked for first."""
    lower = command.lower()
    for name in sorted(_KNOWN, key=len, reverse=True):
        start = lower.find("/" + name)
        while start >= 0:
            end = start + 1 + len(name)
            if end == len(lower) or lower[end].isspace():
                return command[start + 1 : end]
            start = lower.find("/" + name, start + 1)
    words = command.split()
    return os.path.basename(words[0]) if words else ""
