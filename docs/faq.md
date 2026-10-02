# FAQ

## Is KeyEnroll an official Yubico product?

No. It is an independent open-source project, not affiliated with or endorsed by
Yubico, Microsoft, Okta or Ping Identity. It was written because Yubico's own
YubiEnroll tool is a command-line program for Windows only.

## Does it need YubiEnroll to be installed?

No. KeyEnroll does not use YubiEnroll at all. It only reuses the *application
registration* at the identity provider that YubiEnroll's documentation describes.

## How can it work on macOS and Linux if YubiEnroll does not?

Talking to a security key is done by the open-source python-fido2 library — the same
one Yubico builds its own macOS and Linux tools on — and registering the key at the
identity provider is a series of ordinary HTTPS requests. The protocol spoken with
the key is identical on every system; only the way the USB device is opened differs.

This is a well-founded expectation rather than a confirmed fact: as of this writing
nobody has reported enrolling a key with the macOS or Linux package. See
[what has been tested](index.md#what-has-been-tested).

## Which security keys work?

Any FIDO2 key can be reset, given a PIN and enrolled. The serial number and firmware
version are read from YubiKeys. Options such as minimum PIN length, forced PIN change
and "always UV" need a key with recent firmware; see
[Profiles](profiles.md#what-the-key-has-to-support).

## Why does Windows ask for administrator rights every time?

Windows reserves direct access to FIDO security keys for elevated processes.
Ordinary programs have to go through the Windows Hello dialogs, which cannot reset a
key or set its options. This is a property of Windows, not of KeyEnroll.

## Why do Windows and macOS warn me when I install it?

The installers are not digitally signed, because code-signing certificates and an
Apple developer account cost money. The source code and the build scripts are public,
and the installers are built by GitHub's servers from that source. See
[Installation](install.md).

## Does KeyEnroll see my administrator password?

No. You sign in on the identity provider's own page in your browser. KeyEnroll
receives a token that lets it act on your behalf, and stores it in the credential
store of the operating system.

## Where is the PIN stored? Can I look it up later?

Nowhere, and no. A PIN is shown once after the enrollment and is kept in the bulk
list while the application runs. If it is lost, the key has to be enrolled again
with a factory reset.

## Can the user change the PIN?

Yes, at any time, with the tools of their operating system (for example *Sign-in
options → Security key* in Windows settings) or with Yubico Authenticator. With
*Force PIN change before use* they are made to do so at first use.

## Can I enroll several keys for one user?

Yes. Enroll them one after another; give them names that tell them apart, for
instance with the serial number. Identity providers limit the number of keys per user.

## Can one key be used for several users or tenants?

A key can hold credentials for many accounts. Enroll it **without factory reset**
for the second account, otherwise the first credential is erased.

## Does it send any data to the author?

No. There is no telemetry. The only connection besides your identity provider is the
update check, and only when you press the button. See
[Data and security](data.md#what-keyenroll-communicates-with).

## Which languages are available?

The application: English, German, Spanish, French, Italian and Polish. This
documentation: English and Polish.

## I found a bug or miss a feature.

Please open an issue on the
[project page](https://github.com/inowakowski/KeyEnroll/issues). Describe what you
did and what happened, and mention the version, your operating system and the
identity provider. See [Reporting a problem](troubleshooting.md#reporting-a-problem).

## May I use it in my company? May I modify it?

Yes to both. KeyEnroll is released under the MIT licence: free to use, also
commercially, and free to modify and redistribute as long as the licence text is
kept. It comes without warranty. The bundled libraries have their own licences,
listed in `THIRD-PARTY-NOTICES.md` in every package.
