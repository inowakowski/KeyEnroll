# Identity providers

Before the first sign-in, an **application has to be registered** at the identity
provider. It tells the provider that KeyEnroll may sign administrators in and manage
users' security keys on their behalf.

KeyEnroll uses the **same registration as Yubico's YubiEnroll tool**. Yubico
publishes step-by-step instructions with screenshots for each provider; follow them,
then copy the resulting values into a KeyEnroll [instance](instances.md):

[YubiEnroll: identity provider setup](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html){ .md-button }

This page lists, per provider, the fields KeyEnroll asks for, what it requests from
the provider, and the points that most often go wrong.

!!! info "Common to all providers"
    - The application is registered as a **public (native) client** using the
      *authorization code* flow with PKCE. KeyEnroll holds no client secret.
    - The **redirect URI** must start with `http://localhost` and match the
      registration exactly. During sign-in KeyEnroll listens on that address on your
      own computer only.
    - The default redirect URIs still contain the word `yubienroll`, so that a
      registration made for YubiEnroll works unchanged. If you register a different
      URI, enter the same one in the instance.

## Microsoft Entra ID

| Field | What to enter |
|---|---|
| **Directory (tenant) ID** | From the *Overview* page of the app registration. |
| **Application (client) ID** | From the same page. |
| **Redirect URI** | Default `http://localhost/yubienroll-redirect`. |
| **Entra ID endpoint** | Leave `https://login.microsoftonline.com`. Change only for national clouds. |
| **Microsoft Graph endpoint** | Leave `https://graph.microsoft.com`. Change only for national clouds. |

**Permissions requested** (delegated, Microsoft Graph): `User.ReadBasic.All` and
`UserAuthenticationMethod.ReadWrite.All`. An administrator has to grant consent for
the tenant.

**Role of the signed-in administrator:** *Authentication Administrator*, or
*Privileged Authentication Administrator* to manage the keys of other administrators.

**Check in the tenant:**

- In *Authentication methods → Passkey (FIDO2)*, the method is enabled for the users
  concerned and **Allow self-service setup** is on.
- If the policy restricts keys by AAGUID or enforces attestation, the keys you hand
  out have to satisfy it.

**Good to know:** the name of a key is limited to 30 characters.

## Okta

| Field | What to enter |
|---|---|
| **Okta domain** | For example `example.okta.com`, or your custom domain. |
| **Client ID** | Of the application created for enrollment. |
| **Redirect URI** | Default `http://localhost:8080/yubienroll-redirect`. |

**Scopes requested:** `openid`, `offline_access`, `okta.users.read`,
`okta.users.manage`. The two Okta API scopes have to be granted to the application.

**Role of the signed-in administrator:** one that may manage users and their
authenticators.

**Good to know:**

- A security key is registered **for one domain**. A key enrolled through
  `example.okta.com` does not work on a custom domain of the same organisation, and
  the other way round. Enter the domain your users actually sign in to.
- Okta names the key itself, after its model. The *Key display name* field is ignored.
- Port 8080 has to be free on your computer during sign-in.

## PingOne PingID

| Field | What to enter |
|---|---|
| **Environment ID** | Of the PingOne environment. |
| **Client ID** | Of the application created for enrollment. |
| **Redirect URI** | Default `http://localhost:9443/yubienroll-callback`. |
| **Region** | The region of your PingOne environment: North America, Europe, Canada, Asia-Pacific, Australia or Singapore. |
| **Custom domain** | Optional. Only if the environment uses a custom domain. |
| **MFA policy ID** | Optional. Leave empty to use the default MFA policy. |

**Role of the signed-in administrator:** one that may read users and manage their
MFA devices in the environment.

**Good to know:** the FIDO policy of the environment decides which keys are accepted.

## PingOne Advanced Identity Cloud

| Field | What to enter |
|---|---|
| **Tenant** | The host name of the tenant, for example `openam-example.forgeblocks.com`. |
| **Realm** | Default `alpha`. |
| **Journey name** | The WebAuthn registration journey created for enrollment. |
| **Client ID** | Of the OAuth 2.0 client created for enrollment. |
| **Redirect URI** | Default `http://localhost:8443/yubienroll-redirect`. |
| **WebAuthn origin** | Optional. Leave empty to use the address of the tenant. |

**Scopes requested:** `openid`, `profile`, `fr:idm:*`.

**Check in the tenant:**

- In the *WebAuthn Registration Node* of the journey, **Return challenge as
  JavaScript** is switched **off**.

**Limitations:** this provider offers no interface for listing or deleting
credentials, so the [Credentials](credentials.md) page is not available. Manage them
in the administration console.

## Has it been tested?

Only the **Okta** integration has been confirmed against a live tenant so far. The
other three are implemented from the providers' public API documentation and are
covered by automated tests with simulated responses; expect that a detail may need
fixing, and please [report it](https://github.com/inowakowski/KeyEnroll/issues).
