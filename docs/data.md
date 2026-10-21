# Data and security

What KeyEnroll stores, where, and what never leaves the application.

## Where things are kept

| What | Where | Contains secrets? |
|---|---|---|
| Settings: instances, profiles, appearance, language, message template, window layout | `config.json` in the settings folder | No. Tenant and client IDs are identifiers, not secrets. |
| Sign-in (refresh token) of each instance | The credential store of the operating system | Yes — protected by the operating system, tied to your user account. |
| Log | `logs/keyenroll.log` in the settings folder | No PINs and no tokens. |
| Deployment log | `journal/deployments-<year>-<month>.csv` in the settings folder | No PINs and no tokens, but names of people. See [below](#the-deployment-log). |
| Temporary PINs | Only in the memory of the running application | They exist on disk only in files **you** export or save. |

The settings folder:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\KeyEnroll` |
| macOS | `~/Library/Application Support/KeyEnroll` |
| Linux | `~/.config/keyenroll` |

*Settings → Open the folder with settings and logs* opens it.

The credential store is the Windows Credential Manager, the macOS Keychain, or the
Secret Service (GNOME Keyring, KWallet) on Linux. If none of them is available,
KeyEnroll does not fall back to a file: the sign-in is simply not remembered.

On macOS and Linux the settings folder is closed to other accounts on the computer.
On Windows the folder is inside your user profile, which is private already.

## PINs

- A random PIN is generated on your computer, with the random number generator of
  the operating system intended for secrets.
- It is sent to the security key over an encrypted channel defined by the FIDO
  standard. It is **never sent to the identity provider** or anywhere else.
- It is shown in the result window, and kept in the bulk list until you clear the
  list or close the application. It is never written to the settings or to the log.
- A PIN or message you copy is removed from the clipboard after one minute, unless
  you have copied something else in the meantime, and also when the application
  closes. It is marked as a secret,
  which asks the Windows clipboard history and its cloud sync, clipboard managers
  on macOS and KDE's Klipper not to record it.
- Files you export or save contain the PIN in plain text. On macOS and Linux they are
  readable by your user only, even if they replace an older file. On Windows they
  get the permissions of the folder you save them in, so choose a folder that only
  you can open. Delete them when the keys have been handed out.

## What this does not protect against

No desktop application can protect its data from the account it runs under:

- **Software running as you** — malware, or anyone using your unlocked session —
  can read the stored sign-in from the credential store, read PINs while they are
  on screen or in the bulk list, and read files you exported.
- **PINs in memory** cannot be reliably wiped from a running program. They are gone
  when the application closes; do not leave a finished bulk list open.
- **A clipboard manager that ignores the secret marker** keeps a copied PIN.
- **The e-mail draft** hands the PIN to your mail program, which stores drafts and
  sent messages by its own rules.

What limits the damage: a temporary PIN is useless without the physical key, and
with *Force PIN change before use* it stops working the first time the user signs
in. Use an administrator workstation you trust, lock it when you leave, and sign
out of KeyEnroll on a computer you share.

## What KeyEnroll communicates with

| Destination | When | What |
|---|---|---|
| Your identity provider | Sign-in, user search, enrollment, credential list | The requests needed for those actions, authorised with your sign-in. |
| The security key | Enrollment | FIDO commands over USB or NFC. |
| `api.github.com` | When you press **Check for updates**, or at start-up if you switched that on | A request for the latest release number. Nothing about you or your tenant is sent. |
| `github.com` | Only when you confirm an update | The download of the release file. |

There is no telemetry, no usage statistics and no background connection unless you
switch on the update check at start-up.

## Updates

!!! info "Since version 0.7.0"

When you confirm an update, KeyEnroll downloads the file from the project's own
release on GitHub and uses it only if its SHA-256 checksum is the one GitHub
publishes for it; a file that differs is deleted at once. Once the project's release
key is built into the application, the list of checksums must also carry the
maintainer's signature, made with a key that is never stored on GitHub. Then even
someone who took over the GitHub account could not slip in a file of their own.

The installers are not signed with a commercial certificate, so Windows and macOS
may still warn about an unknown publisher the first time.

## The log

The log records what the application did and any errors, to make a problem report
useful. It is limited to four files of 1 MB each; older entries are overwritten.

It contains names of users you enrolled and addresses of your tenant, so read it
before you attach it to a public issue.

## The deployment log

!!! info "Since version 0.6.0"

Every enrollment, single or bulk, successful or failed, adds one line to a CSV file
for the month. It answers the questions of an audit: who enrolled which key for
whom, and when.

| Column | Content |
|---|---|
| `time` | Date and time in UTC. |
| `result`, `mode` | `enrolled` or `failed`; `single` or `bulk`. |
| `instance`, `provider`, `operator` | Where the key was registered, and the administrator account that was signed in, as the identity provider names it. |
| `username`, `user_id`, `display_name` | The user who received the key. |
| `serial`, `firmware`, `aaguid`, `key_name` | The key: serial number, firmware version, model and the name it was registered under. |
| `profile`, `pin_changed`, `pin_change_forced` | The profile used, whether the PIN was set, and whether the key now forces the user to change it. |
| `message` | Why an enrollment failed, or a warning, in English so that logs of operators working in different languages can be compared. |

**A PIN is never written to the deployment log.** It does contain names of people,
which in the EU makes it personal data: KeyEnroll deletes months older than the
period set in [Settings → Deployment log](settings.md#deployment-log) (12 months
by default), and the log can be switched off there. On macOS and Linux the files
are readable by your user only.

The administrator's name comes from the sign-in. If the identity provider does not
say it (some PingOne configurations), the column holds the account's identifier, or
stays empty until the next sign-in.

## If the settings file is damaged

If `config.json` cannot be read, KeyEnroll does not overwrite it. The file is set
aside under a name ending in `.unreadable-<date>`, the application starts with
default settings and tells you so. Stored sign-ins are not affected.

## Removing everything

1. Sign out of every instance (this removes the stored sign-ins), or delete the
   instances.
2. Uninstall the application.
3. Delete the settings folder. It also holds the deployment log.

## Reporting a security problem

Please do not describe a vulnerability in a public issue. Contact the maintainer
privately first, through the contact details on the
[project page](https://github.com/inowakowski/KeyEnroll).
