from __future__ import annotations

from ..config import Instance
from ..secrets_store import TokenStore
from .base import (
    AuthRequired,
    Credential,
    DirectoryGroup,
    DirectoryUser,
    FieldSpec,
    Provider,
    ProviderError,
    Registration,
)
from .entra import EntraProvider
from .okta import OktaProvider
from .pingone import PingOneProvider
from .pingone_aic import PingOneAicProvider

PROVIDERS: dict[str, type[Provider]] = {
    p.kind: p
    for p in (EntraProvider, OktaProvider, PingOneProvider, PingOneAicProvider)
}


def create_provider(instance: Instance, token_store: TokenStore) -> Provider:
    try:
        cls = PROVIDERS[instance.kind]
    except KeyError:
        raise ProviderError(f"Unknown identity provider type: {instance.kind}") from None
    return cls(instance.id, instance.settings, token_store)


def keeps_sign_in(
    old_kind: str, old_settings: dict[str, str], new_kind: str, new_settings: dict[str, str]
) -> bool:
    """Whether the sign-in saved for an instance may be kept after its settings
    changed. Another provider type, host, tenant or client ID means no: the
    saved refresh token would otherwise be sent to an address that did not
    issue it."""
    cls = PROVIDERS.get(new_kind)
    return cls is not None and old_kind == new_kind and cls.keeps_sign_in(old_settings, new_settings)


def acceptable_settings(kind: str, settings: dict[str, str]) -> bool:
    """Imported settings are taken only if every address in them is https."""
    cls = PROVIDERS.get(kind)
    return cls is not None and not cls.insecure_settings(settings)


__all__ = [
    "AuthRequired",
    "Credential",
    "DirectoryGroup",
    "DirectoryUser",
    "FieldSpec",
    "PROVIDERS",
    "Provider",
    "ProviderError",
    "Registration",
    "acceptable_settings",
    "create_provider",
    "keeps_sign_in",
]
