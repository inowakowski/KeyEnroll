"""German translations, keyed by the English source string."""

DE = {
    # -- navigation, header, session
    "Enroll": "Registrierung",
    "Credentials": "Anmeldeinformationen",
    "Profiles": "Profile",
    "Instances": "Instanzen",
    "(no instances configured)": "(keine Instanzen eingerichtet)",
    "Signed in": "Angemeldet",
    "Not signed in": "Nicht angemeldet",
    "Sign in": "Anmelden",
    "Sign out": "Abmelden",
    "Complete the sign-in in your browser…": "Schließen Sie die Anmeldung im Browser ab…",
    "Sign-in failed": "Anmeldung fehlgeschlagen",
    "Not signed in. Sign in to the identity provider first.": (
        "Nicht angemeldet. Melden Sie sich zuerst beim Identitätsanbieter an."
    ),
    "The session has expired. Sign in to the identity provider again.": (
        "Die Sitzung ist abgelaufen. Melden Sie sich erneut beim Identitätsanbieter an."
    ),
    "Windows only lets administrators access FIDO security keys directly. Restart the "
    "application as administrator to detect and enroll keys.": (
        "Windows erlaubt nur Administratoren den direkten Zugriff auf "
        "FIDO-Sicherheitsschlüssel. Starten Sie die Anwendung als Administrator neu, um "
        "Schlüssel zu erkennen und zu registrieren."
    ),
    "Restart as administrator": "Als Administrator neu starten",
    "Enrollment in progress": "Registrierung läuft",
    "An enrollment is in progress. Cancel it and quit?": (
        "Eine Registrierung läuft gerade. Abbrechen und die Anwendung beenden?"
    ),
    # -- common
    "Error": "Fehler",
    "Cancel": "Abbrechen",
    "Save": "Speichern",
    "Delete": "Löschen",
    "Edit": "Bearbeiten",
    "Close": "Schließen",
    "Refresh": "Aktualisieren",
    "Search": "Suchen",
    "Searching…": "Suche läuft…",
    "Name": "Name",
    "Created": "Erstellt",
    "Details": "Details",
    "ID": "ID",
    "User": "Benutzer",
    "Username": "Benutzername",
    "Display name": "Anzeigename",
    "E-mail": "E-Mail",
    "Name, username or e-mail": "Name, Benutzername oder E-Mail",
    "{count} user(s) found": "{count} Benutzer gefunden",
    "No instance": "Keine Instanz",
    "Add an identity provider instance first.": (
        "Fügen Sie zuerst eine Instanz eines Identitätsanbieters hinzu."
    ),
    "(none)": "(keines)",
    "(optional)": "(optional)",
    # -- enroll page
    "1. User": "1. Benutzer",
    "2. Security key": "2. Sicherheitsschlüssel",
    "3. Enrollment options": "3. Registrierungsoptionen",
    "Profile": "Profil",
    "Key display name": "Anzeigename des Schlüssels",
    "e.g. YubiKey 5 NFC": "z. B. YubiKey 5 NFC",
    "Enroll security key": "Schlüssel registrieren",
    "No security key detected": "Kein Sicherheitsschlüssel erkannt",
    "Insert a security key or place it on the NFC reader.": (
        "Stecken Sie einen Sicherheitsschlüssel ein oder legen Sie ihn auf das NFC-Lesegerät."
    ),
    "PIN is set": "PIN festgelegt",
    "No PIN set": "Keine PIN festgelegt",
    "minimum PIN length {length}": "PIN-Mindestlänge {length}",
    "always UV enabled": "„UV immer verlangen“ aktiviert",
    "Enterprise Attestation enabled": "Enterprise Attestation aktiviert",
    "PIN change required": "PIN-Änderung erforderlich",
    "no support for advanced options": "erweiterte Optionen werden nicht unterstützt",
    "Sign in to the identity provider first.": (
        "Melden Sie sich zuerst beim Identitätsanbieter an."
    ),
    "No user": "Kein Benutzer ausgewählt",
    "Search for a user and select one from the list.": (
        "Suchen Sie einen Benutzer und wählen Sie ihn in der Liste aus."
    ),
    "No security key": "Kein Sicherheitsschlüssel",
    "Confirm enrollment": "Registrierung bestätigen",
    "User: {user}": "Benutzer: {user}",
    "Security key: {key}": "Sicherheitsschlüssel: {key}",
    "The key will be factory reset. All FIDO credentials on it will be erased.": (
        "Der Schlüssel wird auf die Werkseinstellungen zurückgesetzt. Alle darauf "
        "gespeicherten FIDO-Anmeldeinformationen werden gelöscht."
    ),
    "Cancelling…": "Wird abgebrochen…",
    "Enrollment failed": "Registrierung fehlgeschlagen",
    # -- profile options
    "Factory reset the security key": "Schlüssel auf Werkseinstellungen zurücksetzen",
    "Erases all FIDO credentials and the PIN on the key.": (
        "Löscht alle FIDO-Anmeldeinformationen und die PIN auf dem Schlüssel."
    ),
    "Set new random PIN": "Neue zufällige PIN festlegen",
    "Random PIN length": "Länge der zufälligen PIN",
    "Minimum PIN length": "PIN-Mindestlänge",
    "Force PIN change before use": "PIN-Änderung vor der ersten Verwendung erzwingen",
    "Require always UV": "Benutzerverifizierung (UV) immer verlangen",
    "The key asks for the PIN on every use.": (
        "Der Schlüssel verlangt bei jeder Verwendung die PIN."
    ),
    "Require Enterprise Attestation": "Enterprise Attestation verlangen",
    # -- profiles page
    "New profile": "Neues Profil",
    "Profile name": "Profilname",
    "Profile settings": "Profileinstellungen",
    "Delete profile": "Profil löschen",
    "Delete profile '{name}'?": "Profil „{name}“ löschen?",
    "A profile with this name already exists.": (
        "Ein Profil mit diesem Namen ist bereits vorhanden."
    ),
    "Profile name cannot be empty.": "Der Profilname darf nicht leer sein.",
    "Minimum PIN length must be between 4 and 63.": (
        "Die PIN-Mindestlänge muss zwischen 4 und 63 liegen."
    ),
    "Random PIN length must be between 4 and 63.": (
        "Die Länge der zufälligen PIN muss zwischen 4 und 63 liegen."
    ),
    "Random PIN length cannot be shorter than the minimum PIN length.": (
        "Die zufällige PIN darf nicht kürzer sein als die PIN-Mindestlänge."
    ),
    # -- credentials page
    "FIDO credentials of the selected user": (
        "FIDO-Anmeldeinformationen des ausgewählten Benutzers"
    ),
    "Delete selected": "Auswahl löschen",
    "Delete credential": "Anmeldeinformationen löschen",
    "Delete credential '{name}' of {user}? The user will no longer be able to sign in "
    "with this key.": (
        "Anmeldeinformationen „{name}“ von {user} löschen? Der Benutzer kann sich danach "
        "nicht mehr mit diesem Schlüssel anmelden."
    ),
    "{provider} does not offer an API for listing or deleting credentials. Manage them "
    "in the provider's admin console.": (
        "{provider} bietet keine API zum Auflisten oder Löschen von Anmeldeinformationen. "
        "Verwalten Sie diese in der Verwaltungskonsole des Anbieters."
    ),
    # -- instances page and dialog
    "Identity provider instances": "Instanzen von Identitätsanbietern",
    "Each instance is one tenant of an identity provider. Add as many as you need and "
    "switch between them with the selector at the top.": (
        "Jede Instanz entspricht einem Mandanten (Tenant) eines Identitätsanbieters. Fügen "
        "Sie beliebig viele hinzu und wechseln Sie mit der Auswahl oben im Fenster "
        "zwischen ihnen."
    ),
    "Add instance": "Instanz hinzufügen",
    "Edit instance": "Instanz bearbeiten",
    "Set as active": "Als aktiv festlegen",
    "Delete instance": "Instanz löschen",
    "Delete instance '{name}' and its saved sign-in?": (
        "Instanz „{name}“ und die gespeicherte Anmeldung löschen?"
    ),
    "Session": "Sitzung",
    "Instance name": "Name der Instanz",
    "e.g. Production tenant": "z. B. Produktionsmandant",
    "Identity provider": "Identitätsanbieter",
    "Default profile": "Standardprofil",
    "Use the values of the application registered for YubiEnroll at the identity "
    "provider. The redirect URI must match the registration exactly.": (
        "Verwenden Sie die Werte der beim Identitätsanbieter für YubiEnroll registrierten "
        "Anwendung. Die Umleitungs-URI muss genau mit der Registrierung übereinstimmen."
    ),
    "Instance name cannot be empty.": "Der Name der Instanz darf nicht leer sein.",
    "An instance with this name already exists.": (
        "Eine Instanz mit diesem Namen ist bereits vorhanden."
    ),
    "Required field is empty: {field}": "Pflichtfeld ist leer: {field}",
    "The redirect URI must start with http://localhost.": (
        "Die Umleitungs-URI muss mit http://localhost beginnen."
    ),
    "Settings": "Einstellungen",
    "Language": "Sprache",
    # -- provider settings
    "Directory (tenant) ID": "Verzeichnis-ID (Mandant)",
    "Application (client) ID": "Anwendungs-ID (Client)",
    "Client ID": "Client-ID",
    "Redirect URI": "Umleitungs-URI",
    "Entra ID endpoint": "Entra ID-Endpunkt",
    "Microsoft Graph endpoint": "Microsoft Graph-Endpunkt",
    "Change only for national cloud deployments.": (
        "Nur für nationale Clouds (National Cloud) ändern."
    ),
    "Okta domain": "Okta-Domäne",
    "FIDO2 credentials are registered per domain (default or custom).": (
        "FIDO2-Anmeldeinformationen werden pro Domäne registriert (Standarddomäne oder "
        "benutzerdefinierte Domäne)."
    ),
    "Environment ID": "Environment ID",
    "Region": "Region",
    "Custom domain": "Benutzerdefinierte Domäne",
    "MFA policy ID": "ID der MFA-Richtlinie",
    "Only if the environment uses a custom domain.": (
        "Nur wenn die Umgebung eine benutzerdefinierte Domäne verwendet."
    ),
    "Leave empty to use the default MFA policy.": (
        "Leer lassen, um die Standard-MFA-Richtlinie zu verwenden."
    ),
    "Tenant": "Tenant",
    "Realm": "Realm",
    "Journey name": "Name der Journey",
    "WebAuthn origin": "WebAuthn-Origin",
    "The WebAuthn registration journey created for YubiEnroll.": (
        "Die für YubiEnroll erstellte Journey zur WebAuthn-Registrierung."
    ),
    "Leave empty to use the tenant address.": (
        "Leer lassen, um die Adresse des Tenants zu verwenden."
    ),
    # -- PIN dialogs
    "Security key PIN": "PIN des Sicherheitsschlüssels",
    "Enter the current PIN of the security key:": (
        "Geben Sie die aktuelle PIN des Sicherheitsschlüssels ein:"
    ),
    "Wrong PIN.": "Falsche PIN.",
    "Attempts remaining: {retries}": "Verbleibende Versuche: {retries}",
    "Show PIN": "PIN anzeigen",
    "New PIN": "Neue PIN",
    "Repeat PIN": "PIN wiederholen",
    "Choose a PIN of at least {length} characters.": (
        "Wählen Sie eine PIN mit mindestens {length} Zeichen."
    ),
    "The PIN is too short.": "Die PIN ist zu kurz.",
    "The PINs do not match.": "Die PINs stimmen nicht überein.",
    "The security key rejected this PIN (too short or too simple).": (
        "Der Sicherheitsschlüssel hat diese PIN abgelehnt (zu kurz oder zu einfach)."
    ),
    # -- result dialog
    "Enrollment complete": "Registrierung abgeschlossen",
    "The security key has been enrolled.": "Der Sicherheitsschlüssel wurde registriert.",
    "Serial number": "Seriennummer",
    "Temporary PIN:": "Temporäre PIN:",
    "The PIN you entered has been set on the key.": (
        "Die von Ihnen eingegebene PIN wurde auf dem Schlüssel festgelegt."
    ),
    "The PIN of the key was not changed.": "Die PIN des Schlüssels wurde nicht geändert.",
    "The user must change the PIN before first use.": (
        "Der Benutzer muss die PIN vor der ersten Verwendung ändern."
    ),
    # -- enrollment engine: progress
    "Checking sign-in and permissions…": "Anmeldung und Berechtigungen werden geprüft…",
    "Factory reset: remove the security key now…": (
        "Zurücksetzen: Entfernen Sie jetzt den Sicherheitsschlüssel…"
    ),
    "Factory reset: insert the security key again…": (
        "Zurücksetzen: Stecken Sie den Sicherheitsschlüssel wieder ein…"
    ),
    "Factory reset: touch the security key to confirm…": (
        "Zurücksetzen: Berühren Sie zur Bestätigung den Sicherheitsschlüssel…"
    ),
    "The security key has been reset.": "Der Sicherheitsschlüssel wurde zurückgesetzt.",
    "Setting the PIN…": "PIN wird festgelegt…",
    "Changing the PIN…": "PIN wird geändert…",
    "Setting the minimum PIN length to {length}…": (
        "PIN-Mindestlänge wird auf {length} gesetzt…"
    ),
    "Enabling 'Require always UV'…": "„UV immer verlangen“ wird aktiviert…",
    "Enabling Enterprise Attestation…": "Enterprise Attestation wird aktiviert…",
    "Requesting a registration challenge…": "Registrierungs-Challenge wird angefordert…",
    "Touch the security key to create the credential…": (
        "Berühren Sie den Sicherheitsschlüssel, um die Anmeldeinformationen zu erstellen…"
    ),
    "Registering the credential with the identity provider…": (
        "Anmeldeinformationen werden beim Identitätsanbieter registriert…"
    ),
    "Forcing a PIN change before first use…": (
        "PIN-Änderung vor der ersten Verwendung wird erzwungen…"
    ),
    "Done.": "Fertig.",
    # -- enrollment engine: errors
    "Enrollment cancelled.": "Registrierung abgebrochen.",
    "No security key detected. Insert a key and try again.": (
        "Kein Sicherheitsschlüssel erkannt. Stecken Sie einen Schlüssel ein und versuchen "
        "Sie es erneut."
    ),
    "The selected security key is no longer connected. Refresh the list.": (
        "Der ausgewählte Sicherheitsschlüssel ist nicht mehr verbunden. Aktualisieren Sie "
        "die Liste."
    ),
    "Timed out waiting for the security key.": (
        "Zeitüberschreitung beim Warten auf den Sicherheitsschlüssel."
    ),
    "The key was not touched in time.": "Der Schlüssel wurde nicht rechtzeitig berührt.",
    "This security key does not support FIDO2.": (
        "Dieser Sicherheitsschlüssel unterstützt FIDO2 nicht."
    ),
    "This security key does not support a PIN.": (
        "Dieser Sicherheitsschlüssel unterstützt keine PIN."
    ),
    "This security key does not support 'Require always UV' (firmware 5.5+ needed).": (
        "Dieser Sicherheitsschlüssel unterstützt „UV immer verlangen“ nicht (Firmware 5.5 "
        "oder neuer erforderlich)."
    ),
    "This security key does not support Enterprise Attestation.": (
        "Dieser Sicherheitsschlüssel unterstützt Enterprise Attestation nicht."
    ),
    "This security key cannot enforce a minimum PIN length or a forced PIN change "
    "(firmware 5.5+ needed).": (
        "Dieser Sicherheitsschlüssel kann weder eine PIN-Mindestlänge noch eine "
        "PIN-Änderung erzwingen (Firmware 5.5 oder neuer erforderlich)."
    ),
    "The reset was not accepted. It must be confirmed within a few seconds of inserting "
    "the key.": (
        "Das Zurücksetzen wurde nicht angenommen. Es muss innerhalb weniger Sekunden nach "
        "dem Einstecken des Schlüssels bestätigt werden."
    ),
    "Factory reset failed.": "Das Zurücksetzen auf die Werkseinstellungen ist fehlgeschlagen.",
    "The current PIN is shorter than the minimum PIN length of the profile. Enable 'Set "
    "new random PIN' or 'Factory reset'.": (
        "Die aktuelle PIN ist kürzer als die PIN-Mindestlänge des Profils. Aktivieren Sie "
        "„Neue zufällige PIN festlegen“ oder das Zurücksetzen auf die Werkseinstellungen."
    ),
    "Too many wrong PIN attempts. Re-insert the key and try again.": (
        "Zu viele falsche PIN-Eingaben. Stecken Sie den Schlüssel neu ein und versuchen "
        "Sie es erneut."
    ),
    "The PIN is blocked. The key must be factory reset.": (
        "Die PIN ist gesperrt. Der Schlüssel muss auf die Werkseinstellungen zurückgesetzt "
        "werden."
    ),
    "This security key is already registered for this user.": (
        "Dieser Sicherheitsschlüssel ist für diesen Benutzer bereits registriert."
    ),
    "The identity provider returned an RP ID that does not match its origin.": (
        "Der Identitätsanbieter hat eine RP-ID zurückgegeben, die nicht zu seinem Origin passt."
    ),
    "The security key reported an error: {detail}": (
        "Der Sicherheitsschlüssel hat einen Fehler gemeldet: {detail}"
    ),
    "The credential was registered, but forcing a PIN change failed: {detail}": (
        "Die Anmeldeinformationen wurden registriert, aber das Erzwingen der PIN-Änderung "
        "ist fehlgeschlagen: {detail}"
    ),
    # -- bulk enrollment
    "Bulk enrollment": "Massenregistrierung",
    "User list": "Benutzerliste",
    "Text or CSV file with one user per line: user name, login or e-mail. In a CSV with "
    "several columns, name the user column 'username'.": (
        "Text- oder CSV-Datei mit einem Benutzer pro Zeile: Benutzername, Anmeldename oder "
        "E-Mail. Benennen Sie in einer CSV-Datei mit mehreren Spalten die Benutzerspalte "
        "„username“."
    ),
    "Load from file…": "Aus Datei laden…",
    "Load user list": "Benutzerliste laden",
    "User lists (*.csv *.txt);;All files (*)": (
        "Benutzerlisten (*.csv *.txt);;Alle Dateien (*)"
    ),
    "No users were found in this file.": "In dieser Datei wurden keine Benutzer gefunden.",
    "Clear list": "Liste leeren",
    "Looking up users in the directory…": "Benutzer werden im Verzeichnis gesucht…",
    "Load a user list to begin.": "Laden Sie eine Benutzerliste, um zu beginnen.",
    "Ready. Insert the first security key and press Start.": (
        "Bereit. Stecken Sie den ersten Sicherheitsschlüssel ein und klicken Sie auf „Start“."
    ),
    "This list belongs to another instance. Export the results and clear it.": (
        "Diese Liste gehört zu einer anderen Instanz. Exportieren Sie die Ergebnisse und "
        "leeren Sie die Liste."
    ),
    "Enrollment options": "Registrierungsoptionen",
    "Add the serial number to the key name": "Seriennummer an den Schlüsselnamen anhängen",
    "Show PINs in the list": "PINs in der Liste anzeigen",
    "Start": "Start",
    "Stop": "Stopp",
    "Retry failed": "Fehlgeschlagene wiederholen",
    "Export results…": "Ergebnisse exportieren…",
    "Export results": "Ergebnisse exportieren",
    "Export": "Exportieren",
    "The file will contain the temporary PINs in plain text. Store it securely and delete "
    "it once the keys have been handed out.": (
        "Die Datei enthält die temporären PINs im Klartext. Bewahren Sie sie sicher auf und "
        "löschen Sie sie, sobald die Schlüssel ausgegeben wurden."
    ),
    "Results exported to {path}": "Ergebnisse exportiert nach {path}",
    "Unsaved PINs": "Nicht gespeicherte PINs",
    "The temporary PINs have not been exported and will be lost. Continue?": (
        "Die temporären PINs wurden nicht exportiert und gehen verloren. Fortfahren?"
    ),
    "Start bulk enrollment": "Massenregistrierung starten",
    "{count} security key(s) will be enrolled, one per user.": (
        "Anzahl der zu registrierenden Sicherheitsschlüssel: {count} (einer pro Benutzer)."
    ),
    "Every inserted key will be factory reset. All FIDO credentials on it will be erased.": (
        "Jeder eingesteckte Schlüssel wird auf die Werkseinstellungen zurückgesetzt. Alle "
        "darauf gespeicherten FIDO-Anmeldeinformationen werden gelöscht."
    ),
    "Bulk enrollment paused": "Massenregistrierung angehalten",
    "{count} ready": "{count} bereit",
    "{count} enrolled": "{count} registriert",
    "{count} failed": "{count} fehlgeschlagen",
    "{count} not found": "{count} nicht gefunden",
    "Checking…": "Wird geprüft…",
    "Ready": "Bereit",
    "Not found": "Nicht gefunden",
    "In progress": "Läuft",
    "Enrolled": "Registriert",
    "Failed": "Fehlgeschlagen",
    "Status": "Status",
    "Key name": "Schlüsselname",
    "Temporary PIN": "Temporäre PIN",
    "Enrolled at": "Registriert am",
    "Message": "Meldung",
    "Insert the security key for {user}…": (
        "Stecken Sie den Sicherheitsschlüssel für {user} ein…"
    ),
    "Remove the previous key, then insert the key for {user}…": (
        "Entfernen Sie den vorherigen Schlüssel und stecken Sie dann den Schlüssel für "
        "{user} ein…"
    ),
    "Several security keys are connected. Leave only one connected.": (
        "Es sind mehrere Sicherheitsschlüssel verbunden. Lassen Sie nur einen eingesteckt."
    ),
    "Batch finished.": "Durchlauf abgeschlossen.",
    "Security key {serial} was already enrolled in this batch.": (
        "Der Sicherheitsschlüssel {serial} wurde in diesem Durchlauf bereits registriert."
    ),
    # -- key details and naming
    "Firmware": "Firmware",
    "Ready to enroll.": "Bereit zur Registrierung.",
    "serial number not readable": "Seriennummer nicht lesbar",
    "Key will be registered as: {name}": "Der Schlüssel wird registriert als: {name}",
    "Key name: {name}": "Schlüsselname: {name}",
    # -- profile summary
    "factory reset": "Zurücksetzen auf Werkseinstellungen",
    "no factory reset": "kein Zurücksetzen",
    "random PIN of {length} digits": "zufällige PIN mit {length} Ziffern",
    "PIN entered by the operator": "PIN-Eingabe durch den Bediener",
    "forced PIN change": "erzwungene PIN-Änderung",
    "always UV": "UV immer verlangen",
    "Enterprise Attestation": "Enterprise Attestation",
    # -- appearance
    "Appearance": "Darstellung",
    "Light": "Hell",
    "Dark": "Dunkel",
    "Custom": "Benutzerdefiniert",
    "Custom colours": "Eigene Farben",
    "Accent colour…": "Akzentfarbe…",
    "Choose the accent colour": "Akzentfarbe auswählen",
    "Restart the application to apply the change.": (
        "Starten Sie die Anwendung neu, um die Änderung zu übernehmen."
    ),
    "Version {version}": "Version {version}",
    # -- hand-over to the user
    "Pass it on to the user": "An den Benutzer weitergeben",
    "The message contains the PIN. Send it through a different channel than the key "
    "itself.": (
        "Die Nachricht enthält die PIN. Senden Sie sie auf einem anderen Weg als den "
        "Schlüssel selbst."
    ),
    "Copy PIN": "PIN kopieren",
    "Copy message": "Nachricht kopieren",
    "E-mail draft…": "E-Mail-Entwurf…",
    "Save to file…": "In Datei speichern…",
    "Save message": "Nachricht speichern",
    "Text files (*.txt)": "Textdateien (*.txt)",
    "Copied. The clipboard will be cleared in one minute.": (
        "Kopiert. Die Zwischenablage wird in einer Minute geleert."
    ),
    "Saved to {path}. The file contains the PIN.": (
        "Gespeichert unter {path}. Die Datei enthält die PIN."
    ),
    "The PIN is not stored anywhere. It is shown only in this window.": (
        "Die PIN wird nirgendwo gespeichert. Sie wird nur in diesem Fenster angezeigt."
    ),
    "No e-mail address is known for this user.": (
        "Für diesen Benutzer ist keine E-Mail-Adresse bekannt."
    ),
    "A draft was opened in your e-mail program. Review it and send it.": (
        "In Ihrem E-Mail-Programm wurde ein Entwurf geöffnet. Prüfen und senden Sie ihn."
    ),
    "No e-mail program is available. Copy the message instead.": (
        "Es ist kein E-Mail-Programm verfügbar. Kopieren Sie stattdessen die Nachricht."
    ),
    "security key": "Sicherheitsschlüssel",
    "(provided separately)": "(wird separat mitgeteilt)",
    "You will be asked to set your own PIN the first time you use the key.": (
        "Bei der ersten Verwendung des Schlüssels werden Sie aufgefordert, eine eigene PIN "
        "festzulegen."
    ),
    "Message for the user…": "Nachricht für den Benutzer…",
    "Select an enrolled user to copy, e-mail or save the hand-over message.": (
        "Wählen Sie einen registrierten Benutzer aus, um die Übergabenachricht zu kopieren, "
        "per E-Mail zu senden oder zu speichern."
    ),
    # -- export options
    "CSV files (*.csv)": "CSV-Dateien (*.csv)",
    "Enrolled users only": "Nur registrierte Benutzer",
    "All users on the list, with their status": "Alle Benutzer der Liste mit ihrem Status",
    "Include temporary PINs": "Temporäre PINs einschließen",
    "CSV, semicolon separated": "CSV, durch Semikolons getrennt",
    "CSV, comma separated": "CSV, durch Kommas getrennt",
    "Format": "Format",
    # -- settings page
    "Colour scheme": "Farbschema",
    "Same as the system (light or dark)": "Wie das System (hell oder dunkel)",
    "Same as the system": "Wie das System",
    "Message for the user": "Nachricht für den Benutzer",
    "Used after an enrollment for the e-mail draft, the copied message and the saved "
    "file. Placeholders: {placeholders}.": (
        "Wird nach einer Registrierung für den E-Mail-Entwurf, die kopierte Nachricht und "
        "die gespeicherte Datei verwendet. Platzhalter: {placeholders}."
    ),
    "Subject": "Betreff",
    "Text": "Text",
    "Restore the default text": "Standardtext wiederherstellen",
    "Saved.": "Gespeichert.",
    "The default text has been restored.": "Der Standardtext wurde wiederhergestellt.",
    "About": "Info",
    "Version": "Version",
    "License": "Lizenz",
    "Project page": "Projektseite",
    "Documentation": "Dokumentation",
    "KeyEnroll is an independent open-source project. It is not affiliated with or "
    "endorsed by Yubico, Microsoft, Okta or Ping Identity.": (
        "KeyEnroll ist ein unabhängiges Open-Source-Projekt. Es steht in keiner Verbindung "
        "zu Yubico, Microsoft, Okta oder Ping Identity und wird von diesen nicht unterstützt."
    ),
    "Open the folder with settings and logs": "Ordner mit Einstellungen und Protokollen öffnen",
    # -- unexpected errors
    "An unexpected error occurred:": "Ein unerwarteter Fehler ist aufgetreten:",
    "Details were written to the log: {path}": (
        "Details wurden in das Protokoll geschrieben: {path}"
    ),
    "The settings file could not be read and was set aside as {path}. KeyEnroll started "
    "with default settings.": (
        "Die Einstellungsdatei konnte nicht gelesen werden und wurde als {path} "
        "beiseitegelegt. KeyEnroll wurde mit den Standardeinstellungen gestartet."
    ),
    # -- updates
    "Check for updates": "Nach Updates suchen",
    "Checking for updates…": "Suche nach Updates…",
    "Open the download page": "Downloadseite öffnen",
    "Version {latest} is available (you have {current}).": (
        "Version {latest} ist verfügbar (installiert: {current})."
    ),
    "You have the latest version ({current}).": (
        "Sie verwenden die neueste Version ({current})."
    ),
    "Could not reach the update server. Check the connection.": (
        "Der Update-Server ist nicht erreichbar. Prüfen Sie die Verbindung."
    ),
    "No published release was found.": "Es wurde keine veröffentlichte Version gefunden.",
    "The update server is busy. Try again in a few minutes.": (
        "Der Update-Server ist ausgelastet. Versuchen Sie es in einigen Minuten erneut."
    ),
    "The update server returned an unexpected answer.": (
        "Der Update-Server hat eine unerwartete Antwort geliefert."
    ),
}
