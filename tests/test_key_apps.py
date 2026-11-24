"""Finding and closing other programs that use security keys."""

from __future__ import annotations

import os

from keyenroll.fido import key_apps
from keyenroll.fido.key_apps import AUTHENTICATOR, MANAGER, YUBIENROLL, KeyApp, Process

YA_DIR = r"C:\Program Files\Yubico\Yubico Authenticator"


def test_yubico_programs_are_found_and_grouped():
    processes = [
        Process(10, "authenticator.exe", YA_DIR + r"\authenticator.exe"),
        Process(11, "authenticator-helper.exe", YA_DIR + r"\helper\authenticator-helper.exe"),
        Process(12, "ykman-gui.exe"),
        Process(13, "explorer.exe", r"C:\Windows\explorer.exe"),
        Process(14, "Yubico Authenticator", "/Applications/Yubico Authenticator.app/..."),
        Process(15, "yubienroll.exe", r"C:\Program Files\Yubico\YubiEnroll\yubienroll.exe"),
    ]
    found = key_apps.find(processes)
    assert [(a.name, a.pids) for a in found] == [
        (AUTHENTICATOR, [10, 11, 14]),
        (MANAGER, [12]),
        (YUBIENROLL, [15]),
    ]


def test_generic_names_count_only_in_a_yubico_folder():
    processes = [
        Process(20, "authenticator.exe", r"C:\Tools\authenticator.exe"),
        Process(21, "authenticator.exe"),  # path unreadable
        Process(22, "OktaAuthenticatorService.exe", r"C:\Program Files\Okta\x.exe"),
    ]
    assert key_apps.find(processes) == []


def test_own_process_is_never_reported():
    assert key_apps.find([Process(os.getpid(), "ykman.exe")]) == []


def test_executable_names_are_read_from_command_lines():
    assert (
        key_apps._name_in("/Applications/Yubico Authenticator.app/Contents/MacOS/Yubico Authenticator")
        == "Yubico Authenticator"
    )
    assert key_apps._name_in("/opt/yubico-authenticator/helper/authenticator-helper -v") == (
        "authenticator-helper"
    )
    assert key_apps._name_in("/usr/bin/python3 -m keyenroll") == "python3"


def test_listing_the_running_processes_includes_this_one():
    assert os.getpid() in {p.pid for p in key_apps.running()}


def test_close_ends_the_processes_and_reports_what_is_left(monkeypatch):
    alive = {
        30: Process(30, "ykman-gui.exe"),
        31: Process(31, "yubioath-desktop.exe"),
    }
    stubborn = {31}
    ended = []

    def terminate(pid):
        ended.append(pid)
        if pid not in stubborn:
            alive.pop(pid)

    monkeypatch.setattr(key_apps, "_terminate", terminate)
    monkeypatch.setattr(key_apps, "running", lambda: list(alive.values()))

    left = key_apps.close(key_apps.find(), timeout=0.3)

    assert sorted(ended) == [30, 31]
    assert left == [KeyApp(AUTHENTICATOR, [31])]
