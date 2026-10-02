"""Enrollment engine: prepares the security key according to a profile,
creates the FIDO credential and registers it with the identity provider."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Collection, Protocol

from fido2.client import (
    ClientError,
    DefaultClientDataCollector,
    Fido2Client,
    UserInteraction,
)
from fido2.ctap import CtapDevice, CtapError
from fido2.ctap2 import Ctap2
from fido2.ctap2.config import Config
from fido2.ctap2.pin import ClientPin

from ..config import Profile
from ..i18n import N_
from ..providers import DirectoryUser, Provider
from .devices import DeviceSource, KeyInfo, close, device_key
from .pin import generate_pin

logger = logging.getLogger(__name__)

ERR = CtapError.ERR
POLL_INTERVAL = 0.4
REINSERT_TIMEOUT = 120
RESET_ATTEMPTS = 3


class EnrollError(Exception):
    """Carries an untranslated message template and its parameters."""

    def __init__(self, template: str, **params):
        super().__init__(template.format(**params) if params else template)
        self.template = template
        self.params = params


class EnrollCancelled(EnrollError):
    def __init__(self):
        super().__init__(N_("Enrollment cancelled."))


class EnrollUI(Protocol):
    """Callbacks invoked from the enrollment thread."""

    def status(self, template: str, **params) -> None: ...

    def ask_current_pin(self, retries: int | None, wrong: bool) -> str | None: ...

    def ask_new_pin(self, min_length: int, rejected: bool) -> str | None: ...


@dataclass
class EnrollResult:
    user: DirectoryUser
    key: KeyInfo
    pin: str | None = None  # set only when a random PIN was generated
    pin_changed: bool = False
    display_name: str = ""  # name the credential was registered under
    warnings: list[tuple[str, dict]] = field(default_factory=list)


def compose_key_name(base: str, serial: int | None, limit: int | None = None) -> str:
    """Appends the serial number to the key's display name.

    When the provider limits the name length, the base name is shortened so
    that the serial number is never cut off.
    """
    base = base.strip()
    if not serial:
        return base[:limit] if limit else base
    suffix = str(serial)
    if not base:
        base = "YubiKey"
    if limit:
        base = base[: max(0, limit - len(suffix) - 1)].rstrip()
    return f"{base} {suffix}".strip()


class _Interaction(UserInteraction):
    def __init__(self, pin: str, ui: EnrollUI):
        self._pin = pin
        self._ui = ui

    def prompt_up(self) -> None:
        self._ui.status(N_("Touch the security key to create the credential…"))

    def request_pin(self, permissions, rp_id):
        return self._pin

    def request_uv(self, permissions, rp_id):
        return True


class Enroller:
    def __init__(
        self,
        provider: Provider,
        profile: Profile,
        user: DirectoryUser,
        display_name: str,
        device_key: str | None,
        ui: EnrollUI,
        source: DeviceSource | None = None,
        cancel: threading.Event | None = None,
        append_serial: bool = False,
        try_reset_first: bool = False,
        used_serials: Collection[int] = (),
    ):
        self.provider = provider
        self.profile = profile
        self.user = user
        self.display_name = display_name
        self.device_key = device_key
        self.ui = ui
        self.source = source or DeviceSource()
        self.cancel = cancel or threading.Event()
        self.append_serial = append_serial
        # The key was inserted moments ago, so a reset may be accepted
        # without asking the operator to re-insert it.
        self.try_reset_first = try_reset_first
        # Serial numbers that must not be enrolled (again) in this session.
        self.used_serials = used_serials

    # -- helpers -----------------------------------------------------------

    def _check_cancel(self) -> None:
        if self.cancel.is_set():
            raise EnrollCancelled()

    def _scan(self) -> dict[str, CtapDevice]:
        return {device_key(d): d for d in self.source.list()}

    def _open_device(self) -> CtapDevice:
        devices = self._scan()
        if not devices:
            raise EnrollError(N_("No security key detected. Insert a key and try again."))
        if self.device_key is None and len(devices) == 1:
            self.device_key = next(iter(devices))
        chosen = devices.pop(self.device_key, None) if self.device_key else None
        for other in devices.values():
            close(other)
        if chosen is None:
            raise EnrollError(
                N_("The selected security key is no longer connected. Refresh the list.")
            )
        return chosen

    def _wait_for(self, predicate, timeout: float):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._check_cancel()
            result = predicate()
            if result is not None:
                return result
            self.cancel.wait(POLL_INTERVAL)
        raise EnrollError(N_("Timed out waiting for the security key."))

    def _config(self, ctap: Ctap2, pin: str) -> Config:
        client_pin = ClientPin(ctap)
        token = client_pin.get_pin_token(pin, ClientPin.PERMISSION.AUTHENTICATOR_CFG)
        return Config(ctap, client_pin.protocol, token)

    # -- steps -------------------------------------------------------------

    def _precheck(self, info) -> None:
        p = self.profile
        options = info.options
        if "clientPin" not in options:
            raise EnrollError(N_("This security key does not support a PIN."))
        can_configure = bool(options.get("authnrCfg"))
        if p.require_always_uv and not (can_configure and "alwaysUv" in options):
            raise EnrollError(
                N_("This security key does not support 'Require always UV' (firmware 5.5+ needed).")
            )
        if p.require_ea and not (can_configure and "ep" in options):
            raise EnrollError(
                N_("This security key does not support Enterprise Attestation.")
            )
        wants_min_pin = p.min_pin_length > info.min_pin_length
        if (wants_min_pin or p.force_pin_change) and not (
            can_configure and options.get("setMinPINLength")
        ):
            raise EnrollError(
                N_(
                    "This security key cannot enforce a minimum PIN length or a "
                    "forced PIN change (firmware 5.5+ needed)."
                )
            )

    def _try_reset(self, dev: CtapDevice) -> EnrollError | None:
        """Sends the reset. Returns None on success, or a retryable error; the
        device is closed whenever the reset did not succeed."""
        self.ui.status(N_("Factory reset: touch the security key to confirm…"))
        try:
            Ctap2(dev).reset(event=self.cancel)
        except CtapError as e:
            close(dev)
            self._check_cancel()
            if e.code in (ERR.NOT_ALLOWED, ERR.OPERATION_DENIED):
                return EnrollError(
                    N_(
                        "The reset was not accepted. It must be confirmed "
                        "within a few seconds of inserting the key."
                    )
                )
            if e.code in (ERR.ACTION_TIMEOUT, ERR.USER_ACTION_TIMEOUT):
                return EnrollError(N_("The key was not touched in time."))
            raise EnrollError(
                N_("The security key reported an error: {detail}"), detail=e.code.name
            ) from e
        except BaseException:
            close(dev)
            raise
        self.device_key = device_key(dev)
        self.ui.status(N_("The security key has been reset."))
        return None

    def _reset(self, dev: CtapDevice) -> CtapDevice:
        key = device_key(dev)
        if self.try_reset_first:
            error = self._try_reset(dev)
            if error is None:
                return dev
            self.ui.status(error.template)
        else:
            close(dev)
        others = set(self._scan_keys()) - {key}

        def removed():
            return True if key not in self._scan_keys() else None

        def inserted():
            devices = self._scan()
            new = [k for k in devices if k not in others]
            chosen = devices.pop(new[0]) if new else None
            for other in devices.values():
                close(other)
            return chosen

        last_error: EnrollError | None = None
        for _ in range(RESET_ATTEMPTS):
            self.ui.status(N_("Factory reset: remove the security key now…"))
            self._wait_for(removed, REINSERT_TIMEOUT)
            self.ui.status(N_("Factory reset: insert the security key again…"))
            dev = self._wait_for(inserted, REINSERT_TIMEOUT)
            key = device_key(dev)
            last_error = self._try_reset(dev)
            if last_error is None:
                return dev
            self.ui.status(last_error.template)
        raise last_error or EnrollError(N_("Factory reset failed."))

    def _scan_keys(self) -> list[str]:
        devices = self._scan()
        for dev in devices.values():
            close(dev)
        return list(devices)

    def _new_pin(self, min_length: int, rejected: bool) -> tuple[str, bool]:
        """Returns (pin, generated)."""
        p = self.profile
        if p.random_pin:
            return generate_pin(max(p.random_pin_length, min_length)), True
        while True:
            pin = self.ui.ask_new_pin(min_length, rejected)
            if pin is None:
                raise EnrollCancelled()
            if len(pin) >= min_length:
                return pin, False
            rejected = True

    def _set_new_pin(self, apply, min_length: int) -> tuple[str, bool]:
        """Chooses a PIN and applies it; asks again if the key rejects it."""
        rejected = False
        while True:
            pin, generated = self._new_pin(min_length, rejected)
            try:
                apply(pin)
                return pin, generated
            except CtapError as e:
                if e.code != ERR.PIN_POLICY_VIOLATION:
                    raise
                rejected = True

    def _prepare_pin(self, ctap: Ctap2, result: EnrollResult) -> str:
        p = self.profile
        info = ctap.get_info()
        client_pin = ClientPin(ctap)
        min_length = max(p.min_pin_length, info.min_pin_length)

        if not info.options.get("clientPin"):
            self.ui.status(N_("Setting the PIN…"))
            pin, generated = self._set_new_pin(client_pin.set_pin, min_length)
            result.pin_changed = True
            result.pin = pin if generated else None
            return pin

        current = self._verify_current_pin(client_pin, info)
        if p.random_pin or info.force_pin_change:
            self.ui.status(N_("Changing the PIN…"))
            pin, generated = self._set_new_pin(
                lambda new: client_pin.change_pin(current, new), min_length
            )
            result.pin_changed = True
            result.pin = pin if generated else None
            return pin

        if len(current) < p.min_pin_length:
            raise EnrollError(
                N_(
                    "The current PIN is shorter than the minimum PIN length of the "
                    "profile. Enable 'Set new random PIN' or 'Factory reset'."
                )
            )
        return current

    def _verify_current_pin(self, client_pin: ClientPin, info) -> str:
        force_change = info.force_pin_change
        # Without authnrCfg the key only issues legacy tokens (no permissions).
        permissions = (
            ClientPin.PERMISSION.AUTHENTICATOR_CFG
            if info.options.get("authnrCfg")
            else None
        )
        wrong = False
        while True:
            self._check_cancel()
            try:
                retries = client_pin.get_pin_retries()[0]
            except CtapError:
                retries = None
            pin = self.ui.ask_current_pin(retries, wrong)
            if not pin:
                raise EnrollCancelled()
            if force_change:
                # No token can be issued until the PIN is changed; the change
                # itself verifies the current PIN.
                return pin
            try:
                client_pin.get_pin_token(pin, permissions)
                return pin
            except CtapError as e:
                if e.code == ERR.PIN_INVALID:
                    wrong = True
                elif e.code == ERR.PIN_AUTH_BLOCKED:
                    raise EnrollError(
                        N_("Too many wrong PIN attempts. Re-insert the key and try again.")
                    ) from e
                elif e.code == ERR.PIN_BLOCKED:
                    raise EnrollError(
                        N_("The PIN is blocked. The key must be factory reset.")
                    ) from e
                else:
                    raise

    def _configure(self, ctap: Ctap2, pin: str) -> None:
        p = self.profile
        info = ctap.get_info()
        if p.min_pin_length > info.min_pin_length:
            self.ui.status(
                N_("Setting the minimum PIN length to {length}…"), length=p.min_pin_length
            )
            self._config(ctap, pin).set_min_pin_length(min_pin_length=p.min_pin_length)
        if p.require_always_uv and not info.options.get("alwaysUv"):
            self.ui.status(N_("Enabling 'Require always UV'…"))
            self._config(ctap, pin).toggle_always_uv()
        if p.require_ea and not info.options.get("ep"):
            self.ui.status(N_("Enabling Enterprise Attestation…"))
            self._config(ctap, pin).enable_enterprise_attestation()

    def _make_credential(self, dev: CtapDevice, registration, pin: str):
        options = dict(registration.options)
        # The ceremony is bounded by the provider's challenge lifetime and the
        # operator's cancel button rather than a browser-style timeout.
        options.pop("timeout", None)
        if self.profile.require_ea:
            options["attestation"] = "enterprise"
        client = Fido2Client(
            dev,
            DefaultClientDataCollector(registration.origin),
            user_interaction=_Interaction(pin, self.ui),
        )
        try:
            return client.make_credential(options, event=self.cancel)
        except ClientError as e:
            self._check_cancel()
            raise self._client_error(e) from e

    @staticmethod
    def _client_error(e: ClientError) -> EnrollError:
        code = e.code
        if code == ClientError.ERR.DEVICE_INELIGIBLE:
            return EnrollError(
                N_("This security key is already registered for this user.")
            )
        if code == ClientError.ERR.TIMEOUT:
            return EnrollError(N_("The key was not touched in time."))
        if code == ClientError.ERR.BAD_REQUEST and e.cause is None:
            return EnrollError(
                N_("The identity provider returned an RP ID that does not match its origin.")
            )
        cause = e.cause
        detail = cause.code.name if isinstance(cause, CtapError) else str(cause or code.name)
        return EnrollError(N_("The security key reported an error: {detail}"), detail=detail)

    # -- main --------------------------------------------------------------

    def run(self) -> EnrollResult:
        p = self.profile
        self.ui.status(N_("Checking sign-in and permissions…"))
        self.provider.preflight(self.user)
        self._check_cancel()

        dev = self._open_device()
        try:
            try:
                ctap = Ctap2(dev)
            except (ValueError, CtapError) as e:
                raise EnrollError(N_("This security key does not support FIDO2.")) from e
            self._precheck(ctap.info)
            result = EnrollResult(user=self.user, key=self.source.describe(dev))
            self.ui.status(N_("Security key: {key}"), key=result.key.label)
            if result.key.serial and result.key.serial in self.used_serials:
                raise EnrollError(
                    N_("Security key {serial} was already enrolled in this batch."),
                    serial=result.key.serial,
                )
            result.display_name = (
                compose_key_name(
                    self.display_name,
                    result.key.serial,
                    getattr(self.provider, "max_display_name", None),
                )
                if self.append_serial
                else self.display_name
            )

            if p.reset:
                dev = self._reset(dev)
                ctap = Ctap2(dev)
                result.key = self.source.describe(dev)

            try:
                pin = self._prepare_pin(ctap, result)
                self._configure(ctap, pin)
            except CtapError as e:
                self._check_cancel()
                raise EnrollError(
                    N_("The security key reported an error: {detail}"), detail=e.code.name
                ) from e
            self._check_cancel()

            self.ui.status(N_("Requesting a registration challenge…"))
            registration = self.provider.begin_registration(self.user)
            try:
                response = self._make_credential(dev, registration, pin)
                self.ui.status(N_("Registering the credential with the identity provider…"))
                self.provider.complete_registration(
                    registration, response, result.display_name
                )
            except BaseException:
                try:
                    self.provider.cancel_registration(registration)
                except Exception:
                    logger.warning("Cleaning up the registration failed", exc_info=True)
                raise

            if p.force_pin_change:
                self.ui.status(N_("Forcing a PIN change before first use…"))
                try:
                    self._config(ctap, pin).set_min_pin_length(force_change_pin=True)
                except CtapError as e:
                    result.warnings.append(
                        (
                            N_("The credential was registered, but forcing a PIN change failed: {detail}"),
                            {"detail": e.code.name},
                        )
                    )
            result.key = self.source.describe(dev)
            self.ui.status(N_("Done."))
            return result
        finally:
            close(dev)
