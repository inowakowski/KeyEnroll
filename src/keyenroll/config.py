"""Persistent configuration: provider instances, enrollment profiles, settings.

Secrets (refresh tokens) are never written here, see secrets_store.py.
"""

from __future__ import annotations

import json
import logging
import os
import re
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
# What happens when a profile requires a minimum firmware version and the
# version of the key cannot be read (NFC, keys other than YubiKeys).
UNKNOWN_FIRMWARE = ("refuse", "warn")


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


def append_private(path: str | Path, data: bytes) -> None:
    """Adds to a file that only the owner can read, creating it if needed."""
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "ab") as f:
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


def version_tuple(text: str | None) -> tuple[int, ...] | None:
    """'5.7.1' -> (5, 7, 1); None for anything that is not a version number."""
    if not text or not re.fullmatch(r"\s*\d+(\.\d+){0,3}\s*", text):
        return None
    parts = [int(p) for p in text.strip().split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()  # 5.7 and 5.7.0 are the same version
    return tuple(parts)


def normalize_aaguid(text: str) -> str | None:
    """An AAGUID in its usual form (lower case, with hyphens), or None."""
    try:
        return str(uuid.UUID(text.strip()))
    except (ValueError, AttributeError, TypeError):
        return None


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
    # Key models the profile accepts, as {"aaguid": ..., "name": ...};
    # empty accepts every model.
    allowed_models: list[dict[str, str]] = field(default_factory=list)
    min_firmware: str = ""  # empty: no requirement
    unknown_firmware: str = "refuse"

    @property
    def allowed_aaguids(self) -> set[str]:
        return {m["aaguid"] for m in self.allowed_models}

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
        if self.min_firmware.strip() and version_tuple(self.min_firmware) is None:
            out.append(N_("Minimum firmware must be a version number such as 5.7."))
        return out

    @classmethod
    def from_dict(cls, data: dict) -> Profile:
        known = {f.name for f in fields(cls)}
        profile = cls(**{k: v for k, v in data.items() if k in known})
        # Hand-edited or imported files: keep what makes sense, drop the rest.
        models = []
        for entry in profile.allowed_models if isinstance(profile.allowed_models, list) else []:
            aaguid = normalize_aaguid(entry.get("aaguid", "")) if isinstance(entry, dict) else None
            if aaguid and aaguid not in {m["aaguid"] for m in models}:
                models.append({"aaguid": aaguid, "name": str(entry.get("name") or "")})
        profile.allowed_models = models
        profile.min_firmware = str(profile.min_firmware or "").strip()
        if profile.unknown_firmware not in UNKNOWN_FIRMWARE:
            profile.unknown_firmware = "refuse"
        return profile


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
        # Deployment log (journal.py) and how many months it is kept.
        self.journal_enabled: bool = True
        self.journal_months: int = 12
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
        self.journal_enabled = bool(data.get("journal_enabled", True))
        try:
            months = int(data.get("journal_months", 12))
        except (TypeError, ValueError):
            months = 12
        self.journal_months = min(max(months, 1), 120)
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
            "journal_enabled": self.journal_enabled,
            "journal_months": self.journal_months,
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


# -- moving the configuration to another workstation --------------------------

EXPORT_FORMAT = "keyenroll-config"
EXPORT_VERSION = 1
MAX_IMPORT_BYTES = 1_000_000
CLASH_MODES = ("skip", "replace", "rename")


def export_config(
    store: ConfigStore,
    instances: bool = True,
    profiles: bool = True,
    message: bool = True,
) -> dict:
    """What another workstation needs to work with the same tenants.

    Never contains a secret: sign-ins stay in the credential store of this
    computer. Instance IDs are left out because the stored sign-ins are filed
    under them; the importing side gives every instance a new one.
    """
    from . import __version__

    data: dict = {"format": EXPORT_FORMAT, "version": EXPORT_VERSION, "app": __version__}
    if instances:
        data["instances"] = [
            {
                "name": i.name,
                "kind": i.kind,
                "settings": dict(i.settings),
                "default_profile": i.default_profile,
            }
            for i in store.instances
        ]
    if profiles:
        data["profiles"] = [asdict(p) for p in store.profiles]
    if message and (store.message_subject or store.message_body):
        data["message"] = {"subject": store.message_subject, "body": store.message_body}
    return data


@dataclass
class ConfigImport:
    """The usable content of an exported configuration file."""

    instances: list[Instance] = field(default_factory=list)
    profiles: list[Profile] = field(default_factory=list)
    message: tuple[str, str] | None = None
    skipped: list[str] = field(default_factory=list)  # names of unusable entries


class ImportProblem(ValueError):
    """Carries an untranslated message for the operator."""


def parse_import(raw: bytes, known_kinds: set[str]) -> ConfigImport:
    if len(raw) > MAX_IMPORT_BYTES:
        raise ImportProblem(N_("The file is too large to be a KeyEnroll configuration."))
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as e:
        raise ImportProblem(N_("The file is not a KeyEnroll configuration.")) from e
    if not isinstance(data, dict) or data.get("format") != EXPORT_FORMAT:
        raise ImportProblem(N_("The file is not a KeyEnroll configuration."))
    version = data.get("version")
    if not isinstance(version, int) or version > EXPORT_VERSION:
        raise ImportProblem(
            N_("The file was made by a newer version of KeyEnroll. Update the application first.")
        )

    out = ConfigImport()
    for entry in data.get("instances") or []:
        name = str(entry.get("name") or "").strip() if isinstance(entry, dict) else ""
        settings = entry.get("settings") if isinstance(entry, dict) else None
        if not name or entry.get("kind") not in known_kinds or not isinstance(settings, dict):
            out.skipped.append(name or "?")
            continue
        default = entry.get("default_profile")
        out.instances.append(
            Instance(
                name=name,
                kind=entry["kind"],
                settings={str(k): str(v) for k, v in settings.items() if v is not None},
                default_profile=str(default) if default else None,
            )
        )
    for entry in data.get("profiles") or []:
        try:
            profile = Profile.from_dict(entry)
            usable = isinstance(profile.name, str) and not profile.problems()
        except (TypeError, AttributeError, ValueError):  # wrong types in a hand-edited file
            usable = False
        if not usable:
            out.skipped.append(str(entry.get("name") or "?") if isinstance(entry, dict) else "?")
            continue
        out.profiles.append(profile)
    message = data.get("message")
    if isinstance(message, dict):
        out.message = (str(message.get("subject") or ""), str(message.get("body") or ""))
    return out


@dataclass
class ImportOutcome:
    added: int = 0
    replaced: int = 0
    skipped: int = 0
    # Instances whose settings were replaced: (id, the provider type changed).
    replaced_instances: list[tuple[str, bool]] = field(default_factory=list)


def _free_name(name: str, taken: set[str]) -> str:
    n = 2
    while f"{name} ({n})" in taken:
        n += 1
    return f"{name} ({n})"


def apply_import(
    store: ConfigStore,
    imported: ConfigImport,
    clash: str = "rename",
    instances: bool = True,
    profiles: bool = True,
    message: bool = True,
) -> ImportOutcome:
    """Adds the imported entries; ``clash`` says what to do with a name that
    exists already: keep ours, replace ours, or add theirs under a new name."""
    outcome = ImportOutcome()
    renamed: dict[str, str] = {}  # imported profile name -> name it got here

    if profiles:
        for profile in imported.profiles:
            existing = store.profile(profile.name)
            if existing is None:
                store.profiles.append(profile)
                outcome.added += 1
            elif clash == "replace":
                store.profiles[store.profiles.index(existing)] = profile
                outcome.replaced += 1
            elif clash == "rename":
                new_name = _free_name(profile.name, {p.name for p in store.profiles})
                renamed[profile.name] = new_name
                profile.name = new_name
                store.profiles.append(profile)
                outcome.added += 1
            else:
                outcome.skipped += 1

    if instances:
        for instance in imported.instances:
            default = instance.default_profile
            default = renamed.get(default, default)
            instance.default_profile = default if store.profile(default) else None
            existing = next((i for i in store.instances if i.name == instance.name), None)
            if existing is None:
                store.instances.append(instance)
                outcome.added += 1
            elif clash == "replace":
                # Keeps the ID, and with it the sign-in, unless the provider changed.
                outcome.replaced_instances.append((existing.id, existing.kind != instance.kind))
                existing.kind = instance.kind
                existing.settings = instance.settings
                existing.default_profile = instance.default_profile
                outcome.replaced += 1
            elif clash == "rename":
                instance.name = _free_name(instance.name, {i.name for i in store.instances})
                store.instances.append(instance)
                outcome.added += 1
            else:
                outcome.skipped += 1
        if store.active_instance is None and store.instances:
            store.active_instance_id = store.instances[0].id

    if message and imported.message is not None:
        store.message_subject, store.message_body = imported.message
    store.save()
    return outcome
