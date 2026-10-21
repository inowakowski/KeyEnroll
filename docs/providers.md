# Identity providers

Before the first sign-in, an **application has to be registered** at the identity
provider. It tells the provider that KeyEnroll may sign administrators in and manage
users' security keys on their behalf.

KeyEnroll uses the **same registration as Yubico's YubiEnroll tool**. Yubico
publishes step-by-step instructions with screenshots for each provider; follow them,
then copy the resulting values into a KeyEnroll [instance](instances.md):

[YubiEnroll: identity provider setup](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html){ .md-button }

This page lists, per provider, the fields KeyEnroll asks for, **what the accounts and
the tenant must allow**, and the points that most often go wrong.

!!! info "Common to all providers"
    - The application is registered as a **public (native) client** using the
      *authorization code* flow with PKCE. KeyEnroll holds no client secret.
    - The **redirect URI** must start with `http://localhost` and match the
      registration exactly. During sign-in KeyEnroll listens on that address on your
      own computer only.
    - The default redirect URIs still contain the word `yubienroll`, so that a
      registration made for YubiEnroll works unchanged. If you register a different
      URI, enter the same one in the instance.

## Accounts involved

Three kinds of account take part, and each provider has its own requirements for
them:

1. **The setup administrator** registers the application and grants it permissions,
   once per tenant. This account is not used in KeyEnroll afterwards.
2. **The operator** is the administrator who signs in to KeyEnroll and enrolls keys.
   Everything KeyEnroll does happens with this account's rights: the application
   permissions only open the door, the operator's role decides what is allowed
   behind it.
3. **The user** receives the key. The account has to exist at the provider and be
   allowed to use security keys.

### Administrator roles at a glance { #administrator-roles-at-a-glance }

| Identity provider | Setup administrator | Operator (signs in to KeyEnroll) |
|---|---|---|
| Microsoft Entra ID | *Application Administrator* or *Cloud Application Administrator* to register; admin consent also from *Privileged Role Administrator* or *Global Administrator* | *Authentication Administrator*; *Privileged Authentication Administrator* for keys of other administrators |
| Okta | *Super Administrator* or *Application Administrator* | *Super Administrator*, *Organization Administrator* or *Group Administrator* |
| PingOne PingID | An administrator who may create applications in the environment | *Identity Data Admin* and *Environment Admin* |
| PingOne Advanced Identity Cloud | A tenant administrator (application, journey, script and secrets) | Internal role `openidm-admin`, and whatever the journey's authorization step checks (for example membership in `webauthn-admins`) |

The details, and what the tenant itself has to allow, follow per provider.

## Microsoft Entra ID

| Field | What to enter |
|---|---|
| **Directory (tenant) ID** | From the *Overview* page of the app registration. |
| **Application (client) ID** | From the same page. |
| **Redirect URI** | Default `http://localhost/yubienroll-redirect`. |
| **Entra ID endpoint** | Leave `https://login.microsoftonline.com`. Change only for national clouds. |
| **Microsoft Graph endpoint** | Leave `https://graph.microsoft.com`. Change only for national clouds. |

### App registration

- *App registrations → New registration*, platform **Mobile and desktop
  applications** (public client/native). The redirect URI needs no port: Entra ID
  accepts any port on `localhost`.
- **API permissions**, Microsoft Graph, type **Delegated**:
    - `User.ReadBasic.All`, to find users;
    - `UserAuthenticationMethod.ReadWrite.All`, to enroll, list and delete keys.

    KeyEnroll also asks for the standard `openid`, `profile` and `offline_access`,
    which need no separate entry. Do **not** add *Application* permissions: with
    delegated permissions the application can never do more than the signed-in
    operator.
- **Grant admin consent** for the tenant. Microsoft allows this to a *Privileged Role
  Administrator*, *Cloud Application Administrator* or *Application Administrator*;
  Yubico's guide names the *Global Administrator*.
- Optional: in *Enterprise applications*, set **Assignment required** to *Yes* and
  assign only the operators, so that nobody else can sign in to KeyEnroll.

### Operator

- **Authentication Administrator**: enrolls and manages keys of users who hold no
  administrator role.
- **Privileged Authentication Administrator**: needed for users who hold an
  administrator role themselves, including Global Administrators.
- An operator **cannot enroll a key for their own account**: Microsoft's provisioning
  interface does not support self-service. Use another operator, or the user's own
  *Security info* page.
- The operator's sign-in goes through the tenant's usual multi-factor authentication
  and Conditional Access.

### Tenant settings

In *Entra ID → Authentication methods → Policies → Passkey (FIDO2)*:

- The method is **enabled** and **targeted** at the users who receive keys (*All
  users* or their groups). A member of an *excluded* group cannot get a key, even if
  another group includes them.
- **Allow self-service set up** is **Yes**. Microsoft's provisioning interface
  refuses to work without it (a known issue in Microsoft Graph), even though the
  administrator, not the user, does the setup.
- The passkey profile that applies to the user allows **device-bound** passkeys. If
  it **enforces attestation** or **key restrictions** (an AAGUID allow or block list),
  the key models you hand out have to pass them.

### Users

- Member accounts of the tenant. **Guest (B2B) users** cannot register passkeys.
- In scope of the Passkey (FIDO2) policy, as above.
- No additional licence: passkeys are available in every Entra ID edition, including
  the free one.

### Good to know

- The name of a key is limited to 30 characters.
- Microsoft offers the FIDO2 provisioning API that KeyEnroll uses only in the
  global cloud; the US Government and China (21Vianet) clouds do not support it
  (state of the Microsoft Graph documentation, July 2026). The two endpoint fields
  are there for when that changes.
- Sources: [Yubico: Entra ID](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-entra.html),
  [Microsoft Graph: creationOptions](https://learn.microsoft.com/en-us/graph/api/fido2authenticationmethod-creationoptions?view=graph-rest-1.0),
  [Microsoft: enable passkeys (FIDO2)](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-enable-passkey-fido2).

## Okta

| Field | What to enter |
|---|---|
| **Okta domain** | For example `example.okta.com`, or your custom domain. |
| **Client ID** | Of the application created for enrollment. |
| **Redirect URI** | Default `http://localhost:8080/yubienroll-redirect`. |

### App integration

- *Applications → Create App Integration*, sign-in method **OIDC - OpenID Connect**,
  application type **Native Application**.
- **Grant types**: *Authorization Code* and **Refresh Token**. KeyEnroll asks for
  `offline_access`; without the refresh token grant, sign-in fails.
- **Sign-in redirect URI** with a port, `http://localhost:8080/yubienroll-redirect`
  by default.
- **Assignments**: assign the application to the operators (or to a group they are
  in). An operator who is not assigned cannot sign in to KeyEnroll.
- On the **Okta API Scopes** tab, **grant** `okta.users.read` and
  `okta.users.manage`. KeyEnroll asks for these two together with `openid` and
  `offline_access`.

The setup administrator needs the *Super Administrator* or *Application
Administrator* role.

### Operator

- One of the roles Yubico names: **Super Administrator**, **Organization
  Administrator** or **Group Administrator**. A Group Administrator reaches only the
  users of the groups they administer.
- Okta grants the **intersection** of the application scopes and the operator's
  role: the scopes alone give no rights to an account whose role does not allow
  managing users' authenticators. Other roles, custom ones included, have not been
  tried.

### Tenant settings

- An **Okta Identity Engine** org; that is the edition Yubico lists as supported.
  Classic Engine has not been tried.
- The **FIDO2 (WebAuthn)** authenticator is added and active in *Security →
  Authenticators*. For users to sign in with the key, the authenticator enrollment
  and sign-in policies have to allow it for them.

### Users

- The account exists in Okta.
- The search in KeyEnroll finds users by first name, last name or e-mail. In a
  [bulk list](bulk.md), however, give the **username (login)** or the user ID: Okta
  does not look users up by e-mail address there. The username is often, but not
  necessarily, the e-mail address.

### Good to know

- A security key is registered **for one domain**. A key enrolled through
  `example.okta.com` does not work on a custom domain of the same organisation, and
  the other way round. Enter the domain your users actually sign in to; if they use
  both, enroll through two instances.
- Okta names the key itself, after its model. The *Key display name* field is ignored.
- Port 8080 has to be free on your computer during sign-in.
- Source: [Yubico: Okta](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-okta.html).

## PingOne PingID

| Field | What to enter |
|---|---|
| **Environment ID** | Of the PingOne environment. |
| **Client ID** | Of the application created for enrollment. |
| **Redirect URI** | Default `http://localhost:9443/yubienroll-callback`. |
| **Region** | The region of your PingOne environment: North America, Europe, Canada, Asia-Pacific, Australia or Singapore. |
| **Custom domain** | Optional. Only if the environment uses a custom domain. |
| **MFA policy ID** | Optional. Leave empty to use the default MFA policy. |

### Application

- Application type **Worker**, as in Yubico's guide.
- On the *Configuration* tab, under *OIDC Settings*:
    - **Response type** *Code*; **grant types** *Authorization Code* and *Refresh
      Token*;
    - **PKCE Enforcement** `S256_REQUIRED`;
    - **Token Endpoint Authentication Method** *None*;
    - **Redirect URI** with a port, `http://localhost:9443/yubienroll-callback` by
      default.
- Switch the application **on** (the toggle in the application list).

KeyEnroll asks only for `openid`. What it may do in the PingOne API comes from the
operator's roles, so no further scopes or resources are needed.

### Operator

- The roles **Identity Data Admin** and **Environment Admin**, as Yubico specifies,
  assigned for the environment the users are in.

### Tenant settings

- The environment has **PingOne MFA** (PingID).
- A **FIDO2 policy** exists and is part of the **MFA policy** KeyEnroll uses: the
  environment's default MFA policy, or the one whose ID you enter in the instance.
  The FIDO2 policy decides which keys are accepted (attestation, allowed models).
- If users sign in on a **custom domain**, enter it in the instance, so that the key
  is registered for that domain.

### Users

- The account exists in the PingOne environment the instance points to.

### Good to know

- Port 9443 has to be free on your computer during sign-in.
- Source: [Yubico: PingOne PingID](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-pingone.html).

## PingOne Advanced Identity Cloud

| Field | What to enter |
|---|---|
| **Tenant** | The host name of the tenant, for example `openam-example.forgeblocks.com`. |
| **Realm** | Default `alpha`. |
| **Journey name** | The WebAuthn registration journey created for enrollment. |
| **Client ID** | Of the OAuth 2.0 client created for enrollment. |
| **Redirect URI** | Default `http://localhost:8443/yubienroll-redirect`. |
| **WebAuthn origin** | Optional. Leave empty to use the address of the tenant. |

### OAuth 2.0 client

- *Applications → Custom application*, **OIDC - OpenID Connect**, type
  **Native / SPA**; **Token Endpoint Authentication Method** *None* (public client).
- **Grant types** *Authorization Code* and *Refresh Token*.
- **Scopes** `openid`, `profile`, `fr:idm:*` (under *Show advanced settings*).
- **Redirect URI** with a port, `http://localhost:8443/yubienroll-redirect` by default.
- Registered in the same **realm** as the journey.

### Registration journey

KeyEnroll drives a journey that enrolls the key. It has to look like this:

1. **One username prompt** (a *Page Node* with *Platform Username*, or a *Username
   Collector*). KeyEnroll answers it with the `userName` of the user.
2. Only **server-side nodes** after it, for example *Identify Existing User*, *Scripted
   Decision Node* or *Inner Tree Evaluator*. Any further prompt makes the enrollment
   fail.
3. A **WebAuthn Registration Node**, with **Return challenge as JavaScript** switched
   **off**, and the relying party ID and attestation settings of your environment.
4. A *Success Node*; failed checks lead to a *Failure Node*.

The journey belongs to the realm entered in the instance.

!!! warning "Let the journey check who is enrolling"
    The journey is reachable at the tenant's public sign-in address. Without an
    authorization step, anyone who can start it could register a key for any
    username. KeyEnroll therefore sends the operator's access token with every
    journey call, and Yubico's guide adds a **Scripted Decision Node** that
    introspects that token and checks that the operator belongs to an authorized
    group (`webauthn-admins` in the example). The script needs a separate OAuth 2.0
    client with the scope `am-introspect-all-tokens`, whose ID and secret are kept in
    ESVs (`esv.yubienroll.introspect.client.id`,
    `esv.yubienroll.introspect.client.secret`, `esv.yubienroll.tenant`). Its realm
    has to match yours.

### Operator

- The internal role **`openidm-admin`**: KeyEnroll looks users up through the
  identity management API (`fr:idm:*`).
- Whatever the journey's authorization step checks, for example membership in
  `webauthn-admins`.

### Users

- The account exists as a managed user of the realm (`<realm>_user`) with the
  `userName` KeyEnroll sends to the journey.

### Limitations

This provider offers no interface for listing or deleting credentials, so the
[Credentials](credentials.md) page is not available. Manage them in the
administration console.

Source: [Yubico: PingOne AIC](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-pingone-aic.html).

## Bulk lists from groups

!!! info "Since version 0.7.0"

[Loading a bulk list from a group](bulk.md#loading-the-list-from-a-group) reads group
memberships, which the registration described by YubiEnroll does not allow. It is
therefore **off** until you switch it on for an instance:

1. Grant the additional permission at the identity provider (table below).
2. In KeyEnroll, edit the instance and set **Bulk lists from groups** to **On**.
3. **Sign out and sign in again**, so that the new permission is part of the sign-in.

| Identity provider | Additional permission |
|---|---|
| Microsoft Entra ID | Delegated Microsoft Graph permission `GroupMember.Read.All`, with admin consent for the tenant. |
| Okta | Scope `okta.groups.read`, granted to the application on its *Okta API Scopes* tab. |
| PingOne PingID | No scope; the operator's role has to allow reading groups. *Identity Data Admin*, which enrollment needs anyway, includes that; an operator with a narrower role also needs *Identity Data Read Only*. |
| PingOne Advanced Identity Cloud | No change; `fr:idm:*` already covers groups. Groups are read from the managed object `<realm>_group` and its members through the users' `groups` relationship. **Not yet tried against a live tenant**: if it does not work in your tenant, please [report it](https://github.com/inowakowski/KeyEnroll/issues). |

With the option on and the permission missing, signing in or loading a group ends
with the provider's message about consent or a forbidden request.

## Has it been tested?

Only the **Okta** integration has been confirmed against a live tenant so far. The
other three are implemented from the providers' public API documentation and are
covered by automated tests with simulated responses; expect that a detail may need
fixing, and please [report it](https://github.com/inowakowski/KeyEnroll/issues).

The requirements on this page come from Yubico's YubiEnroll guide and the providers'
own documentation (state of October 2026). Providers rename menus and roles from
time to time; if something here no longer matches your console, please
[report it](https://github.com/inowakowski/KeyEnroll/issues).
