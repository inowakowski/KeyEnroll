# Troubleshooting

Find the message you see, or the situation you are in.

## The key is not detected

| System | Check |
|---|---|
| Windows | The application must run **as administrator**. If a yellow banner is shown, press **Restart as administrator**. |
| Linux | The udev rules for FIDO keys are missing if the key only appears when the application is started as root. Install `libu2f-udev` or `libfido2`, then unplug the key and plug it in again. |
| NFC readers | The PC/SC service has to be running (`pcscd` on Linux; *Smart Card* service on Windows). |
| All | Press **Refresh**. Try another USB port, and avoid unpowered hubs. Close other programs that may be holding the key, such as a browser showing a security key prompt. |

*No security key detected* during an enrollment means the same: the key was not
visible when the enrollment started.

## Signing in

**The browser shows an error about the redirect URI.**
The redirect URI in the instance and the one in the application registration differ.
They must be identical, including the port and the path.

**"Cannot listen on port …".**
Another program on your computer is using the port named in the redirect URI. Close
it, or register a redirect URI with a different port and enter it in the instance.

**The browser finished, but KeyEnroll still waits.**
The browser could not reach `http://localhost`. Some browser security extensions and
corporate proxies block it; allow `localhost`, or use another browser as default.

**"The session has expired."**
Sign in again. How long a sign-in lasts is decided by your identity provider.

**On Linux, you have to sign in after every start.**
No Secret Service is available to store the sign-in. Use a desktop with GNOME
Keyring or KWallet.

## Searching for users

**No user is found.**
With most providers the search matches the *beginning* of the name, user name or
e-mail address. Type the first letters, not a part from the middle. Also check that
the right instance is selected and that the list shows at most 25 matches.

**An error from the provider mentioning permissions or "forbidden".**
The application registration lacks a permission or admin consent, or your account
does not have the required role. See [Identity providers](providers.md).

## During enrollment

| Message | What it means and what to do |
|---|---|
| *The reset was not accepted. It must be confirmed within a few seconds of inserting the key.* | A security key only allows a reset shortly after it is plugged in. Remove it, insert it, and touch it as soon as it blinks. The application retries a few times. |
| *The key was not touched in time.* | Touch the gold contact or the button of the key while it blinks. |
| *Timed out waiting for the security key.* | The key was not removed or re-inserted within two minutes. Start again. |
| *The selected security key is no longer connected.* | The key was unplugged. Insert it and press **Refresh**. |
| *Wrong PIN.* with the remaining attempts | The current PIN of the key was mistyped. Mind the counter: when it reaches zero the PIN is blocked. |
| *Too many wrong PIN attempts. Re-insert the key and try again.* | The key pauses after three wrong PINs in a row. Unplug it and plug it in again. |
| *The PIN is blocked. The key must be factory reset.* | Enable *Factory reset the security key*. All FIDO credentials on the key are lost. |
| *The security key rejected this PIN (too short or too simple).* | The key enforces a PIN policy. Choose a longer or less regular PIN. |
| *The current PIN is shorter than the minimum PIN length of the profile.* | Enable *Set new random PIN* or *Factory reset*, so that a new PIN of sufficient length is set. |
| *This security key does not support …* | The key is too old for an option of the profile, or was not manufactured with it. Use another profile or another key. See [what the key has to support](profiles.md#what-the-key-has-to-support). |
| *This security key is already registered for this user.* | The user already has a credential on this key. Delete it on the [Credentials](credentials.md) page first, or enable the factory reset. |
| *The identity provider returned an RP ID that does not match its origin.* | The domain in the instance is not the one the provider registers keys for. For Okta, enter the domain users sign in to; for PingOne AIC, check *WebAuthn origin*. |
| *The credential was registered, but forcing a PIN change failed.* | The key is enrolled and works with the temporary PIN, but the user will not be made to change it. Tell the user to change the PIN themselves. |
| An error text from the identity provider | Shown as received. Typical causes: the FIDO2 method is not enabled for the user, the tenant's policy does not accept this key model, or a permission is missing. |

## Bulk enrollment

**Many users are "Not found".**
The identifiers in the file are not in the form the provider expects (for example a
short login instead of the full user name), or the wrong instance is selected.

**"Security key … was already enrolled in this batch."**
The same key was inserted for a second user. Take the next key.

**"This list belongs to another instance."**
Switch back to the instance the list was loaded for, or export the results and clear
the list.

**The exported file opens with everything in one column.**
The spreadsheet expects the other separator. Export again and choose the other
format (semicolon or comma).

## The application itself

**A warning that the settings file could not be read.**
See [Data and security](data.md#if-the-settings-file-is-damaged).

**"An unexpected error occurred".**
The details are in the log. Please report it.

## Reporting a problem

1. Note the version (*Settings → About*) and your operating system.
2. If you can, reproduce the problem with detailed logging: start the application
   with `--log-level DEBUG`, see [start-up options](install.md#start-up-options).
3. Open *Settings → Open the folder with settings and logs* and take
   `logs/keyenroll.log`. **Read it first**: it contains user names and tenant
   addresses, though no PINs or tokens.
4. Describe what you did and what happened in the
   [issue tracker](https://github.com/inowakowski/KeyEnroll/issues).
