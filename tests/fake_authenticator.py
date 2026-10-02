"""A software CTAP 2.1 authenticator, enough to exercise the enrollment
engine end to end: clientPIN (protocols 1 and 2), authenticatorConfig,
reset, makeCredential and the getAssertion pre-flight used for exclude lists.
"""

from __future__ import annotations

import os
import struct

from cryptography.hazmat.primitives.asymmetric import ec
from fido2 import cbor
from fido2.ctap import STATUS, CtapDevice, CtapError
from fido2.ctap2.pin import PinProtocolV1, PinProtocolV2
from fido2.hid import CAPABILITY, CTAPHID
from fido2.utils import bytes2int, int2bytes, sha256

ERR = CtapError.ERR
AAGUID = bytes.fromhex("00112233445566778899aabbccddeeff")

PERM_MC = 0x01
PERM_ACFG = 0x20


class _Fail(Exception):
    def __init__(self, code):
        self.code = code


class FakeAuthenticator(CtapDevice):
    def __init__(self, name: str = "fake", supports_config: bool = True):
        self._name = name
        self.supports_config = supports_config
        self.log: list[str] = []
        self.closed = 0
        self._wipe()
        self.fresh = False  # True right after "power-up": reset is allowed

    def _wipe(self):
        self.pin: str | None = None
        self.retries = 8
        self.min_pin_length = 4
        self.always_uv = False
        self.ep = False
        self.force_pin_change = False
        self.credentials: list[dict] = []
        self.token: bytes | None = None
        self.token_permissions = 0
        self._ka = ec.generate_private_key(ec.SECP256R1())
        self.reject_pins: set[str] = set()

    # -- CtapDevice --------------------------------------------------------

    @property
    def capabilities(self) -> int:
        return CAPABILITY.CBOR

    @classmethod
    def list_devices(cls):
        return iter(())

    def close(self) -> None:
        self.closed += 1

    def call(self, cmd, data=b"", event=None, on_keepalive=None):
        if cmd != CTAPHID.CBOR:
            raise CtapError(ERR.INVALID_COMMAND)
        command = data[0]
        params = cbor.decode(data[1:]) if len(data) > 1 else {}
        handler = {
            0x01: self._make_credential,
            0x02: self._get_assertion,
            0x04: self._get_info,
            0x06: self._client_pin,
            0x07: self._reset,
            0x0D: self._config,
        }.get(command)
        if handler is None:
            return bytes([ERR.INVALID_COMMAND])
        self.log.append(handler.__name__.lstrip("_"))
        try:
            result = handler(params, event, on_keepalive)
        except _Fail as e:
            return bytes([e.code])
        return b"\x00" + (cbor.encode(result) if result is not None else b"")

    # -- commands ----------------------------------------------------------

    def _get_info(self, params, event, on_keepalive):
        options = {
            "rk": True,
            "up": True,
            "clientPin": self.pin is not None,
            "pinUvAuthToken": True,
            "makeCredUvNotRqd": True,
        }
        if self.supports_config:
            options.update(
                authnrCfg=True,
                setMinPINLength=True,
                alwaysUv=self.always_uv,
                ep=self.ep,
            )
        return {
            0x01: ["FIDO_2_0", "FIDO_2_1"],
            0x03: AAGUID,
            0x04: dict(sorted(options.items(), key=lambda kv: (len(kv[0]), kv[0]))),
            0x05: 1200,
            0x06: [2, 1],
            0x0C: self.force_pin_change,
            0x0D: self.min_pin_length,
            0x0E: 0x050700,
        }

    def _shared(self, version, peer):
        proto = PinProtocolV2() if version == 2 else PinProtocolV1()
        public = ec.EllipticCurvePublicNumbers(
            bytes2int(peer[-2]), bytes2int(peer[-3]), ec.SECP256R1()
        ).public_key()
        return proto, proto.kdf(self._ka.exchange(ec.ECDH(), public))

    def _check_pin_hash(self, proto, shared, pin_hash_enc):
        if self.pin is None:
            raise _Fail(ERR.PIN_NOT_SET)
        if self.retries == 0:
            raise _Fail(ERR.PIN_BLOCKED)
        self.retries -= 1
        if proto.decrypt(shared, pin_hash_enc) != sha256(self.pin.encode())[:16]:
            self._ka = ec.generate_private_key(ec.SECP256R1())
            raise _Fail(ERR.PIN_INVALID)
        self.retries = 8

    def _store_pin(self, proto, shared, new_pin_enc):
        padded = proto.decrypt(shared, new_pin_enc)
        pin = padded.rstrip(b"\x00").decode()
        if len(pin) < self.min_pin_length or pin in self.reject_pins:
            raise _Fail(ERR.PIN_POLICY_VIOLATION)
        self.pin = pin
        self.force_pin_change = False
        self.token = None

    def _client_pin(self, params, event, on_keepalive):
        version, sub = params.get(1), params[2]
        if sub == 0x01:
            return {3: self.retries}
        if sub == 0x02:
            pn = self._ka.public_key().public_numbers()
            return {1: {1: 2, 3: -25, -1: 1, -2: int2bytes(pn.x, 32), -3: int2bytes(pn.y, 32)}}

        proto, shared = self._shared(version, params[3])
        if sub == 0x03:  # setPIN
            if self.pin is not None:
                raise _Fail(ERR.PIN_AUTH_INVALID)
            if proto.authenticate(shared, params[5]) != params[4]:
                raise _Fail(ERR.PIN_AUTH_INVALID)
            self._store_pin(proto, shared, params[5])
            return None
        if sub == 0x04:  # changePIN
            if proto.authenticate(shared, params[5] + params[6]) != params[4]:
                raise _Fail(ERR.PIN_AUTH_INVALID)
            self._check_pin_hash(proto, shared, params[6])
            self._store_pin(proto, shared, params[5])
            return None
        if sub in (0x05, 0x09):  # getPinToken (legacy / with permissions)
            self._check_pin_hash(proto, shared, params[6])
            if self.force_pin_change:
                raise _Fail(ERR.PIN_POLICY_VIOLATION)
            self.token = os.urandom(32)
            self.token_permissions = params.get(9, 0x03) if sub == 0x09 else 0x03
            return {2: proto.encrypt(shared, self.token)}
        raise _Fail(ERR.INVALID_SUBCOMMAND)

    def _verify_token(self, version, message, param, permission):
        if param is None:
            raise _Fail(ERR.PUAT_REQUIRED)
        proto = PinProtocolV2() if version == 2 else PinProtocolV1()
        if self.token is None or proto.authenticate(self.token, message) != param:
            raise _Fail(ERR.PIN_AUTH_INVALID)
        if not self.token_permissions & permission:
            raise _Fail(ERR.PIN_AUTH_INVALID)

    def _config(self, params, event, on_keepalive):
        if not self.supports_config:
            raise _Fail(ERR.INVALID_COMMAND)
        sub, sub_params = params[1], params.get(2)
        if self.pin is not None:
            message = b"\xff" * 32 + b"\x0d" + struct.pack("<B", sub)
            if sub_params is not None:
                message += cbor.encode(sub_params)
            self._verify_token(params.get(3), message, params.get(4), PERM_ACFG)
        if sub == 0x01:
            self.ep = True
        elif sub == 0x02:
            self.always_uv = not self.always_uv
        elif sub == 0x03:
            new_min = sub_params.get(1)
            if new_min is not None:
                if new_min < self.min_pin_length:
                    raise _Fail(ERR.PIN_POLICY_VIOLATION)
                self.min_pin_length = new_min
                if self.pin is not None and len(self.pin) < new_min:
                    self.force_pin_change = True
            if sub_params.get(3):
                if self.pin is None:
                    raise _Fail(ERR.PIN_NOT_SET)
                self.force_pin_change = True
        else:
            raise _Fail(ERR.INVALID_SUBCOMMAND)
        return None

    def _reset(self, params, event, on_keepalive):
        if not self.fresh:
            raise _Fail(ERR.NOT_ALLOWED)
        if on_keepalive:
            on_keepalive(STATUS.UPNEEDED)
        self._wipe()
        self.fresh = False
        return None

    def _get_assertion(self, params, event, on_keepalive):
        allowed = {c["id"] for c in params.get(3) or []}
        for cred in self.credentials:
            if cred["rp_id"] == params[1] and cred["id"] in allowed:
                auth_data = sha256(cred["rp_id"].encode()) + b"\x00" + struct.pack(">I", 1)
                return {
                    1: {"id": cred["id"], "type": "public-key"},
                    2: auth_data,
                    3: b"\x00" * 64,
                }
        raise _Fail(ERR.NO_CREDENTIALS)

    def _make_credential(self, params, event, on_keepalive):
        client_data_hash, rp, user = params[1], params[2], params[3]
        if self.pin is not None:
            self._verify_token(params.get(9), client_data_hash, params.get(8), PERM_MC)
        elif self.always_uv:
            raise _Fail(ERR.PUAT_REQUIRED)
        for cred in params.get(5) or []:
            if any(c["id"] == cred["id"] and c["rp_id"] == rp["id"] for c in self.credentials):
                raise _Fail(ERR.CREDENTIAL_EXCLUDED)
        if on_keepalive:
            on_keepalive(STATUS.UPNEEDED)
        if event is not None and event.is_set():
            raise _Fail(ERR.KEEPALIVE_CANCEL)

        key = ec.generate_private_key(ec.SECP256R1())
        pn = key.public_key().public_numbers()
        cose = {1: 2, 3: -7, -1: 1, -2: int2bytes(pn.x, 32), -3: int2bytes(pn.y, 32)}
        cred_id = os.urandom(32)
        flags = 0x01 | 0x40 | (0x04 if self.pin is not None else 0)
        auth_data = (
            sha256(rp["id"].encode())
            + bytes([flags])
            + struct.pack(">I", 1)
            + AAGUID
            + struct.pack(">H", len(cred_id))
            + cred_id
            + cbor.encode(cose)
        )
        self.credentials.append(
            {
                "id": cred_id,
                "rp_id": rp["id"],
                "user": user,
                "enterprise": params.get(0x0A),
            }
        )
        self.token = None  # tokens are single-use for makeCredential
        response = {1: "none", 2: auth_data, 3: {}}
        if params.get(0x0A) and self.ep:
            response[4] = True
        return response
