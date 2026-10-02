"""Persistent configuration: provider instances, enrollment profiles, settings.

Secrets (refresh tokens) are never written here, see secrets_store.py.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .i18n import N_

logger = logging.getLogger(__name__)

CONFIG_VERSION = 1
DEFAULT_THEME = "yubico"
MIN_PIN = 4
MAX_PIN = 63


def config_dir() -> Path:
    override = os.environ.get("KEYENROLL_HOME")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "KeyEnroll"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "KeyEnroll"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "keyenroll"


def private_dir(path: Path) -> Path:
    """Creates a folder of ours that only the owner can enter.

    The settings and the log name tenants and users; on a shared macOS or
    Linux machine other accounts have no business reading them. Windows keeps
    %APPDATA% private already. A folder chosen through KEYENROLL_HOME is the
    operator's own and keeps the permissions it was given.
    """
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "posix" and not os.environ.get("KEYENROLL_HOME"):
        try:
            os.chmod(path, 0o700)
        except OSError:
            logger.warning("Could not restrict access to %s", path)
    return path


def write_private(path: str | Path, data: bytes) -> None:
    """Writes a file that only the owner can read, replacing what was there.

    Used for everything that contains a PIN. The mode is set on the open file
    as well, because an existing file keeps its old, possibly wider, mode.
    Windows has no such mode: there the file gets the permissions of its folder.
    """
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        if hasattr(os, "fchmod"):
            os.fchmod(f.fileno(), 0o600)
        f.write(data)


def legacy_config_dir() -> Path | None:
    """Where the app kept its configuration under its former name."""
    if os.environ.get("KEYENROLL_HOME"):
        return None
    current = config_dir()
    old = "yubienroll-gui" if current.name == "keyenroll" else "YubiEnrollGUI"
    return current.with_name(old)


@dataclass
class Profile:
    """Enrollment profile. Defaults mirror the YubiEnroll CLI defaults."""

    name: str = "default"
    min_pin_length: int = 4
    require_always_uv: bool = False
    require_ea: bool = False
    force_pin_change: bool = False
    reset: bool = True
    random_pin: bool = True
    random_pin_length: int = 6

    def problems(self) -> list[str]:
        """Returns untranslated messages describing invalid settings."""
        out = []
        if not self.name.strip():
            out.append(N_("Profile name cannot be empty."))
        if not MIN_PIN <= self.min_pin_length <= MAX_PIN:
            out.append(N_("Minimum PIN length must be between 4 and 63."))
        if self.random_pin:
            if not MIN_PIN <= self.random_pin_length <= MAX_PIN:
                out.append(N_("Random PIN length must be between 4 and 63."))
            elif self.random_pin_length < self.min_pin_length:
                out.append(
                    N_("Random PIN length cannot be shorter than the minimum PIN length.")
                )
        return out

    @classmethod
    def from_dict(cls, data: dict) -> Profile:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Instance:
    """A named configuration of one identity provider tenant."""

    name: str
    kind: str
    settings: dict[str, str] = field(default_factory=dict)
    default_profile: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @classmethod
    def from_dict(cls, data: dict) -> Instance:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


class ConfigStore:
    def __init__(self, path: Path | None = None, legacy_path: Path | None = None):
        self.path = path or config_dir() / "config.json"
        if path is None and legacy_path is None:
            legacy = legacy_config_dir()
            legacy_path = legacy / "config.json" if legacy else None
        self._legacy_path = legacy_path
        self.instances: list[Instance] = []
        self.profiles: list[Profile] = []
        self.active_instance_id: str | None = None
        self.language: str = "auto"
        self.theme: str = DEFAULT_THEME
        self.custom_base: str = "dark"
        self.custom_accent: str = "#4f5bd5"
        self.append_serial: bool = False
        # Hand-over message templates; empty means the built-in text.
        self.message_subject: str = ""
        self.message_body: str = ""
        # Window geometry and similar layout state.
        self.ui: dict[str, str] = {}
        # Set when an unreadable file was moved aside at start-up.
        self.unreadable_backup: Path | None = None
        self.load()

    def _read(self) -> dict:
        # First start after the rename: carry over the old configuration.
        # It is read only; the next save writes to the new location.
        for candidate in (self.path, self._legacy_path):
            if candidate is None:
                continue
            try:
                text = candidate.read_text(encoding="utf-8")
            except FileNotFoundError:
                continue
            data = json.loads(text)
            if not isinstance(data, dict):
                raise ValueError("configuration is not a JSON object")
            return data
        return {}

    def load(self) -> None:
        try:
            data = self._read()
            self._apply(data)
        except (ValueError, TypeError, KeyError, OSError) as e:
            # A damaged file must not keep the application from starting.
            logger.error("Configuration is unreadable (%s); starting with defaults", e)
            self.unreadable_backup = self._set_aside()
            self._apply({})

    def _set_aside(self) -> Path | None:
        backup = self.path.with_name(
            f"{self.path.name}.unreadable-{time.strftime('%Y%m%d-%H%M%S')}"
        )
        try:
            os.replace(self.path, backup)
            return backup
        except OSError:
            return self.path  # could not be moved; it is replaced on the next save

    def _apply(self, data: dict) -> None:
        self.instances = [Instance.from_dict(d) for d in data.get("instances", [])]
        self.profiles = [Profile.from_dict(d) for d in data.get("profiles", [])]
        self.active_instance_id = data.get("active_instance")
        self.language = str(data.get("language", "auto"))
        self.theme = str(data.get("theme", DEFAULT_THEME))
        self.custom_base = str(data.get("custom_base", "dark"))
        self.custom_accent = str(data.get("custom_accent", "#4f5bd5"))
        self.append_serial = bool(data.get("append_serial", False))
        self.message_subject = str(data.get("message_subject", ""))
        self.message_body = str(data.get("message_body", ""))
        ui = data.get("ui", {})
        self.ui = {str(k): str(v) for k, v in ui.items()} if isinstance(ui, dict) else {}
        if not self.profiles:
            self.profiles = [Profile()]
        if self.instance(self.active_instance_id) is None:
            self.active_instance_id = self.instances[0].id if self.instances else None

    def save(self) -> None:
        data = {
            "version": CONFIG_VERSION,
            "language": self.language,
            "theme": self.theme,
            "custom_base": self.custom_base,
            "custom_accent": self.custom_accent,
            "append_serial": self.append_serial,
            "message_subject": self.message_subject,
            "message_body": self.message_body,
            "ui": self.ui,
            "active_instance": self.active_instance_id,
            "instances": [asdict(i) for i in self.instances],
            "profiles": [asdict(p) for p in self.profiles],
        }
        if self.path.parent == config_dir():
            private_dir(self.path.parent)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    # -- instances ---------------------------------------------------------

    def instance(self, instance_id: str | None) -> Instance | None:
        return next((i for i in self.instances if i.id == instance_id), None)

    @property
    def active_instance(self) -> Instance | None:
        return self.instance(self.active_instance_id)

    def upsert_instance(self, instance: Instance) -> None:
        for n, existing in enumerate(self.instances):
            if existing.id == instance.id:
                self.instances[n] = instance
                break
        else:
            self.instances.append(instance)
        if self.active_instance_id is None:
            self.active_instance_id = instance.id
        self.save()

    def delete_instance(self, instance_id: str) -> None:
        self.instances = [i for i in self.instances if i.id != instance_id]
        if self.active_instance_id == instance_id:
            self.active_instance_id = self.instances[0].id if self.instances else None
        self.save()

    def set_active(self, instance_id: str | None) -> None:
        self.active_instance_id = instance_id
        self.save()

    # -- profiles ----------------------------------------------------------

    def profile(self, name: str | None) -> Profile | None:
        return next((p for p in self.profiles if p.name == name), None)

    def upsert_profile(self, profile: Profile, old_name: str | None = None) -> None:
        key = old_name or profile.name
        for n, existing in enumerate(self.profiles):
            if existing.name == key:
                self.profiles[n] = profile
                break
        else:
            self.profiles.append(profile)
        if old_name and old_name != profile.name:
            for inst in self.instances:
                if inst.default_profile == old_name:
                    inst.default_profile = profile.name
        self.save()

    def delete_profile(self, name: str) -> None:
        self.profiles = [p for p in self.profiles if p.name != name]
        for inst in self.instances:
            if inst.default_profile == name:
                inst.default_profile = None
        if not self.profiles:
            self.profiles = [Profile()]
        self.save()
