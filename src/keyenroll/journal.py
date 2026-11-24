"""Deployment log: one line per enrollment, for audit.

Who enrolled which key for whom, and when, in a CSV file per month next to the
settings. A PIN is never written to it. The log names people, so it is kept
for a limited number of months and readable by the owner only.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import append_private, private_dir
from .fido.devices import KeyInfo
from .fido.enroll import EnrollError, EnrollResult
from .providers import Credential, DirectoryUser, ProviderError

logger = logging.getLogger(__name__)

FOLDER = "journal"
FIELDS = (
    "time",
    "result",
    "mode",
    "instance",
    "provider",
    "operator",
    "username",
    "user_id",
    "display_name",
    "serial",
    "firmware",
    "aaguid",
    "key_name",
    "profile",
    "pin_changed",
    "pin_change_forced",
    "message",
)
_FILE = re.compile(r"deployments-(\d{4})-(\d{2})\.csv")
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_lock = threading.Lock()  # single and bulk enrollment never overlap, but be safe


def safe_cell(value) -> str:
    """Neutralises values a spreadsheet would run as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def journal_dir(config_path: Path) -> Path:
    """The log lives next to the settings file it belongs to."""
    return config_path.parent / FOLDER


def _month_file(folder: Path, when: datetime) -> Path:
    return folder / f"deployments-{when:%Y-%m}.csv"


def _message(exc: BaseException) -> str:
    """The reason of a failure in English, so that logs of operators working
    in different languages can be compared."""
    if isinstance(exc, EnrollError):
        return exc.template.format(**exc.params) if exc.params else exc.template
    if isinstance(exc, ProviderError):
        return str(exc)
    return f"{type(exc).__name__}: {exc}"


def _yes_no(value: bool | None) -> str:
    return "" if value is None else ("yes" if value else "no")


@dataclass
class JournalContext:
    instance: str
    provider: str
    operator: str = ""
    profile: str = ""
    mode: str = "single"  # or "bulk"


class Journal:
    """Writes the entries of one enrollment session (a single enrollment or
    one bulk run) to the log in ``folder``."""

    def __init__(self, folder: Path, context: JournalContext, enabled: bool = True):
        self.folder = folder
        self.context = context
        self.enabled = enabled

    def _entry(self, user: DirectoryUser | None, key: KeyInfo | None, **values) -> dict:
        c = self.context
        return {
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": c.mode,
            "instance": c.instance,
            "provider": c.provider,
            "operator": c.operator,
            "profile": c.profile,
            "username": user.username if user else "",
            "user_id": user.id if user else "",
            "display_name": user.display_name if user else "",
            "serial": key.serial if key and key.serial else "",
            "firmware": key.firmware if key and key.firmware else "",
            "aaguid": key.aaguid if key and key.aaguid else "",
            **values,
        }

    def enrolled(self, result: EnrollResult) -> bool:
        warnings = "; ".join(
            template.format(**params) if params else template
            for template, params in result.warnings
        )
        return self.write(
            self._entry(
                result.user,
                result.key,
                result="enrolled",
                key_name=result.display_name,
                pin_changed=_yes_no(result.pin_changed),
                # Read back from the key: false if forcing the change failed.
                pin_change_forced=_yes_no(result.key.force_pin_change),
                message=warnings,
            )
        )

    def failed(
        self, user: DirectoryUser | None, key: KeyInfo | None, exc: BaseException
    ) -> bool:
        return self.write(self._entry(user, key, result="failed", message=_message(exc)))

    def deleted(self, user: DirectoryUser, credential: Credential) -> bool:
        """A credential removed on the Credentials page: the key it was on no
        longer belongs to the user (see ``last_key_owner``)."""
        return self.write(
            self._entry(
                user, None, result="deleted", serial=credential.serial, key_name=credential.name
            )
        )

    def write(self, entry: dict) -> bool:
        """Appends one line. A full disk or a locked file is logged, never
        raised: the enrollment itself has already happened."""
        if not self.enabled:
            return False
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\r\n")
        try:
            with _lock:
                private_dir(self.folder)
                path = _month_file(self.folder, datetime.now(timezone.utc))
                new = not path.exists()
                if new:
                    writer.writerow(FIELDS)
                writer.writerow(safe_cell(entry.get(name, "")) for name in FIELDS)
                data = out.getvalue().encode("utf-8")
                # BOM on a new file only: Excel needs it to read UTF-8.
                append_private(path, (b"\xef\xbb\xbf" if new else b"") + data)
            return True
        except OSError:
            logger.warning("Could not write to the deployment log", exc_info=True)
            return False


def last_key_owner(folder: Path, instance: str, serial) -> DirectoryUser | None:
    """The user the key was last enrolled for with this instance, from this
    computer's log; None if it was never enrolled here or removed since."""
    wanted = str(serial)
    latest: dict | None = None
    try:
        paths = sorted(p for p in folder.iterdir() if _FILE.fullmatch(p.name))
    except OSError:
        return None
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for row in csv.DictReader(io.StringIO(text)):
            if (
                row.get("serial") == wanted
                and row.get("instance") == instance
                and row.get("result") in ("enrolled", "deleted")
                and (latest is None or (row.get("time") or "") >= (latest.get("time") or ""))
            ):
                latest = row
    if latest is None or latest["result"] != "enrolled" or not latest.get("user_id"):
        return None
    return DirectoryUser(
        id=_plain(latest["user_id"]),
        username=_plain(latest.get("username") or ""),
        display_name=_plain(latest.get("display_name") or ""),
    )


def _plain(cell: str) -> str:
    """Undoes ``safe_cell``."""
    return cell[1:] if cell.startswith("'") and cell[1:].startswith(_FORMULA_PREFIXES) else cell


def prune(folder: Path, months: int, today: datetime | None = None) -> list[Path]:
    """Deletes the files of months that ended more than ``months`` ago."""
    today = today or datetime.now(timezone.utc)
    current = today.year * 12 + today.month - 1
    removed = []
    try:
        candidates = list(folder.iterdir())
    except OSError:
        return removed
    for path in candidates:
        match = _FILE.fullmatch(path.name)
        if not match:
            continue
        index = int(match.group(1)) * 12 + int(match.group(2)) - 1
        if index < current - months:
            try:
                path.unlink()
                removed.append(path)
            except OSError:
                logger.warning("Could not delete the old deployment log %s", path)
    if removed:
        logger.info("Deleted %d deployment log file(s) older than %d months", len(removed), months)
    return removed
