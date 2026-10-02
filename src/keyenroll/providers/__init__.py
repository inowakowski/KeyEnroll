from __future__ import annotations

from ..config import Instance
from ..secrets_store import TokenStore
from .base import (
    AuthRequired,
    Credential,
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


__all__ = [
    "AuthRequired",
    "Credential",
    "DirectoryUser",
    "FieldSpec",
    "PROVIDERS",
    "Provider",
    "ProviderError",
    "Registration",
    "create_provider",
]
