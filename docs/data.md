# Data and security

What KeyEnroll stores, where, and what never leaves the application.

## Where things are kept

| What | Where | Contains secrets? |
|---|---|---|
| Settings: instances, profiles, appearance, language, message template, window layout | `config.json` in the settings folder | No. Tenant and client IDs are identifiers, not secrets. |
| Sign-in (refresh token) of each instance | The credential store of the operating system | Yes — protected by the operating system, tied to your user account. |
| Log | `logs/keyenroll.log` in the settings folder | No PINs and no tokens. |
| Temporary PINs | Only in the memory of the running application | They exist on disk only in files **you** export or save. |

The settings folder:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\KeyEnroll` |
| macOS | `~/Library/Application Support/KeyEnroll` |
| Linux | `~/.config/keyenroll` |

*Settings → Open the folder with settings and logs* opens it.

The credential store is the Windows Credential Manager, the macOS Keychain, or the
Secret Service (GNOME Keyring, KWallet) on Linux.

## PINs

- A random PIN is generated on your computer, with the random number generator of
  the operating system intended for secrets.
- It is sent to the security key over an encrypted channel defined by the FIDO
  standard. It is **never sent to the identity provider** or anywhere else.
- It is shown in the result window, and kept in the bulk list until you clear the
  list or close the application. It is never written to the settings or to the log.
- A PIN or message you copy is removed from the clipboard after one minute, unless
  you have copied something else in the meantime.
- Files you export or save contain the PIN in plain text. On macOS and Linux they are
  created readable by your user only. Delete them when the keys have been handed out.

## What KeyEnroll communicates with

| Destination | When | What |
|---|---|---|
| Your identity provider | Sign-in, user search, enrollment, credential list | The requests needed for those actions, authorised with your sign-in. |
| The security key | Enrollment | FIDO commands over USB or NFC. |
| `api.github.com` | Only when you press **Check for updates** | A request for the latest release number. Nothing about you or your tenant is sent. |

There is no telemetry, no usage statistics and no background connection.

## The log

The log records what the application did and any errors, to make a problem report
useful. It is limited to four files of 1 MB each; older entries are overwritten.

It contains names of users you enrolled and addresses of your tenant, so read it
before you attach it to a public issue.

## If the settings file is damaged

If `config.json` cannot be read, KeyEnroll does not overwrite it. The file is set
aside under a name ending in `.unreadable-<date>`, the application starts with
default settings and tells you so. Stored sign-ins are not affected.

## Removing everything

1. Sign out of every instance (this removes the stored sign-ins), or delete the
   instances.
2. Uninstall the application.
3. Delete the settings folder.

## Reporting a security problem

Please do not describe a vulnerability in a public issue. Contact the maintainer
privately first, through the contact details on the
[project page](https://github.com/inowakowski/KeyEnroll).
