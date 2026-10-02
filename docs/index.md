# KeyEnroll

KeyEnroll is a desktop application for **enrolling FIDO2 security keys (YubiKeys) on
behalf of users**. An administrator plugs in a key, picks a user, and the application
prepares the key and registers it with the identity provider, so that the user
receives a key that already works.

It runs on **Windows (x64 and ARM64), macOS and Linux** and is free and open source
(MIT licence).

[Download the latest version](https://github.com/inowakowski/KeyEnroll/releases/latest){ .md-button .md-button--primary }
[Quick start](quickstart.md){ .md-button }

![The Enroll page](assets/screenshots/en/enroll.png){ .shot }

## What it does

| Feature | What it means |
|---|---|
| **Four identity providers** | Microsoft Entra ID, Okta, PingOne PingID and PingOne Advanced Identity Cloud. |
| **Several tenants in one application** | Add as many [instances](instances.md) as you need and switch between them from the top of the window. Each one keeps its own sign-in. |
| **Prepares the key** | Factory reset, a random temporary PIN, minimum PIN length, forced PIN change, "always require user verification", Enterprise Attestation. Stored as reusable [profiles](profiles.md). |
| **Bulk enrollment** | Load a [list of users from a file](bulk.md), enroll one key after another, and export the result with the temporary PINs. |
| **Hand-over to the user** | After an enrollment, [copy a ready message, open an e-mail draft or save a file](enroll.md#handing-the-key-over) with the PIN and the serial number. |
| **Credential overview** | [List and delete](credentials.md) the security keys registered for a user. |
| **Six languages** | English, German, Spanish, French, Italian and Polish. |

## Where to start

<div class="grid cards" markdown>

- **[Installation](install.md)**  
  Download, system requirements, first start on each operating system.
- **[Quick start](quickstart.md)**  
  From an empty application to the first enrolled key in five steps.
- **[The window at a glance](interface.md)**  
  What every part of the window is for.
- **[Identity providers](providers.md)**  
  What has to be configured in Entra ID, Okta and PingOne before the first sign-in.

</div>

## How it relates to YubiEnroll

Yubico publishes a command-line tool called YubiEnroll, available for Windows only.
KeyEnroll is **not a wrapper around it**. It has its own engine: it talks to the key
through the open-source [python-fido2](https://github.com/Yubico/python-fido2) library
and to the identity providers through their public APIs. It uses the same application
registrations at the identity provider that the
[YubiEnroll documentation](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html)
describes, so a tenant prepared for YubiEnroll works with KeyEnroll as well.

!!! note "Independent project"
    KeyEnroll is not affiliated with or endorsed by Yubico, Microsoft, Okta or Ping
    Identity. YubiKey and YubiEnroll are trademarks of Yubico AB; other names belong
    to their owners and are used only to describe compatibility.

## What has been tested

KeyEnroll is young software. Be clear about what is proven before you rely on it:

- Enrollment with **Okta, a USB key, on Windows ARM64** has been confirmed on real
  hardware.
- Everything else — Entra ID, PingOne, PingOne AIC, bulk enrollment, and the macOS,
  Linux and Windows x64 packages — is covered by an automated test suite that uses a
  software security key and simulated provider responses, but **has not yet been
  confirmed against a live tenant with a physical key**.

Try it with a spare key and a test user first, and please
[report what you find](https://github.com/inowakowski/KeyEnroll/issues).
