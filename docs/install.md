# Installation

Installers for every platform are attached to each release on GitHub.

[Open the download page](https://github.com/inowakowski/KeyEnroll/releases/latest){ .md-button .md-button--primary }

| Operating system | File to download |
|---|---|
| Windows 10/11, Intel or AMD | `KeyEnroll-<version>-windows-x64-setup.exe` |
| Windows 11 on ARM | `KeyEnroll-<version>-windows-arm64-setup.exe` |
| macOS, Apple Silicon (M1 and newer) | `KeyEnroll-<version>-macos-arm64.dmg` |
| macOS, Intel | `KeyEnroll-<version>-macos-x64.dmg` |
| Debian, Ubuntu and derivatives | `keyenroll_<version>_amd64.deb` or `keyenroll_<version>_arm64.deb` |
| Other Linux distributions | `KeyEnroll-<version>-linux-x64.tar.gz` or `…-linux-arm64.tar.gz` |

!!! warning "The packages are not digitally signed"
    Code-signing certificates cost money, and this is a free project. Windows
    SmartScreen and macOS Gatekeeper therefore show a warning the first time you start
    the application. The steps below explain how to get past it. Only do so for a
    file you downloaded from the project's own release page.

## Windows

1. Run the `…-setup.exe` file. If SmartScreen shows *Windows protected your PC*,
   choose **More info** and then **Run anyway**.
2. Follow the installer. It needs administrator rights and offers a desktop shortcut.
3. Start KeyEnroll from the Start menu. Windows asks for administrator rights
   (the UAC prompt) **every time the application starts**.

!!! info "Why administrator rights?"
    Windows only lets elevated processes talk to FIDO security keys directly. Without
    them the application starts, but cannot see any key; a yellow banner with a
    **Restart as administrator** button appears in that case.

To remove the application, use *Settings → Apps → Installed apps*. Your settings stay
in place, see [Data and security](data.md).

## macOS

1. Open the `.dmg` file and drag **KeyEnroll** onto the **Applications** folder.
2. Start it from Applications. macOS refuses the first start because the application
   is not notarised. Open *System Settings → Privacy & Security*, scroll down to the
   message about KeyEnroll and choose **Open Anyway**. On older versions of macOS you
   can instead right-click the application and choose **Open**.

No administrator rights are needed. The sign-in to your identity provider is kept in
the macOS Keychain; macOS may ask for permission the first time.

## Linux

=== "Debian / Ubuntu"

    ```bash
    sudo apt install ./keyenroll_<version>_amd64.deb
    ```

    This also installs the recommended packages for security keys and NFC readers.
    Start **KeyEnroll** from the application menu, or run `keyenroll`.

=== "Other distributions"

    ```bash
    tar -xzf KeyEnroll-<version>-linux-x64.tar.gz
    ```

    ```bash
    ./KeyEnroll/KeyEnroll
    ```

Linux needs three things that the installer cannot guarantee on every distribution:

| Requirement | Why | How |
|---|---|---|
| udev rules for FIDO keys | Without them only root can open the key. | Present on most current distributions (systemd 252 or newer). Otherwise install `libu2f-udev` or `libfido2`. |
| A Secret Service (GNOME Keyring, KWallet) | Stores the sign-in. Without it you have to sign in again after every restart of the application. | Part of GNOME and KDE desktops. |
| `pcscd` | Only for keys used over an NFC reader. | `sudo apt install pcscd` |

## Updating

*Settings → About → Check for updates* asks GitHub for the latest published release.
If a newer one exists, a button opens its download page. KeyEnroll never downloads or
installs anything by itself and does not check in the background.

To update, install the new version over the old one. Settings, instances and
profiles are kept.

## Running from source

Developers can run the application directly; see the
[README](https://github.com/inowakowski/KeyEnroll#praca-ze-źródłami) in the repository.

## Start-up options

The installed application accepts a few command-line options, useful when you are
asked for a detailed log:

| Option | Meaning |
|---|---|
| `-l DEBUG`, `--log-level DEBUG` | Log more detail (`ERROR`, `WARNING`, `INFO`, `DEBUG`). |
| `--log-file <path>` | Write the log to this file instead of the default location. |
| `-v`, `--version` | Print the version and exit. |
