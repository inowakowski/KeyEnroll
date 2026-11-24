# Credentials

The **Credentials** page shows which FIDO security keys a user has registered at the
identity provider, and lets you delete one — for example when a key is lost or an
employee returns it.

![The Credentials page](assets/screenshots/en/credentials.png){ .shot }

## The page

**User** (top). When you open the page, it lists **all users** of the directory,
sorted by name, so searching is optional: select a user from the list, or search as
on the [Enroll page](enroll.md#1-user) to narrow it down. **Refresh list** clears
the search and reads the users again; the selected user stays selected. An empty
search lists everyone too. Very large directories show the first 5000 users; search
for the others.

With Okta [keeping serial numbers](providers.md#key-serial-numbers), plugging in a
YubiKey shows a highlighted banner at the top of the page saying who it belongs to,
for example *Connected key S/N 32445513 belongs to: Alice Example*. **Show the
user's keys** selects that user, and the credential on the plugged-in key is
selected, ready to be deleted. The same banner on the [Enroll page](enroll.md)
brings you here.

**FIDO credentials of the selected user** (bottom)

| Column | Meaning |
|---|---|
| **Name** | The name the key was registered under. |
| **Serial number** | With Okta, when the instance [keeps serial numbers](providers.md#key-serial-numbers). Empty otherwise. |
| **Created** | When it was registered. |
| **Details** | What the provider knows about the key, usually its model. |
| **ID** | The provider's identifier of the credential. |

| Button | What it is for |
|---|---|
| **Refresh** | Reads the list again. |
| **Delete selected** | Removes the selected credential from the user's account, after a confirmation. |

!!! danger "Deleting cannot be undone"
    The user can no longer sign in with that key as soon as the credential is
    deleted. To use the key again it has to be enrolled again. Deleting here does
    not touch the key itself: its PIN and its other credentials stay as they are.

## What each provider supports

| Identity provider | List | Delete |
|---|---|---|
| Microsoft Entra ID | yes | yes |
| Okta | yes | yes |
| PingOne PingID | yes | yes |
| PingOne Advanced Identity Cloud | no | no |

PingOne Advanced Identity Cloud does not offer an interface for this; manage the
credentials in its administration console instead. The page says so when such an
instance is selected.
