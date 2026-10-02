"""Polish translations, keyed by the English source string."""

PL = {
    # -- navigation, header, session
    "Enroll": "Rejestracja",
    "Credentials": "Poświadczenia",
    "Profiles": "Profile",
    "Instances": "Instancje",
    "(no instances configured)": "(brak skonfigurowanych instancji)",
    "Signed in": "Zalogowano",
    "Not signed in": "Nie zalogowano",
    "Sign in": "Zaloguj",
    "Sign out": "Wyloguj",
    "Complete the sign-in in your browser…": "Dokończ logowanie w przeglądarce…",
    "Sign-in failed": "Logowanie nie powiodło się",
    "Not signed in. Sign in to the identity provider first.": (
        "Nie zalogowano. Najpierw zaloguj się do dostawcy tożsamości."
    ),
    "The session has expired. Sign in to the identity provider again.": (
        "Sesja wygasła. Zaloguj się ponownie do dostawcy tożsamości."
    ),
    "Windows only lets administrators access FIDO security keys directly. Restart the "
    "application as administrator to detect and enroll keys.": (
        "Windows pozwala na bezpośredni dostęp do kluczy FIDO tylko administratorom. "
        "Uruchom aplikację ponownie jako administrator, aby wykrywać i rejestrować klucze."
    ),
    "Restart as administrator": "Uruchom jako administrator",
    "Enrollment in progress": "Rejestracja w toku",
    "An enrollment is in progress. Cancel it and quit?": (
        "Trwa rejestracja klucza. Przerwać ją i zamknąć aplikację?"
    ),
    # -- common
    "Error": "Błąd",
    "Cancel": "Anuluj",
    "Save": "Zapisz",
    "Delete": "Usuń",
    "Edit": "Edytuj",
    "Close": "Zamknij",
    "Refresh": "Odśwież",
    "Search": "Szukaj",
    "Searching…": "Wyszukiwanie…",
    "Name": "Nazwa",
    "Created": "Utworzono",
    "Details": "Szczegóły",
    "ID": "ID",
    "User": "Użytkownik",
    "Username": "Nazwa użytkownika",
    "Display name": "Nazwa wyświetlana",
    "E-mail": "E-mail",
    "Name, username or e-mail": "Imię i nazwisko, nazwa użytkownika lub e-mail",
    "{count} user(s) found": "Znaleziono użytkowników: {count}",
    "No instance": "Brak instancji",
    "Add an identity provider instance first.": (
        "Najpierw dodaj instancję dostawcy tożsamości."
    ),
    "(none)": "(brak)",
    "(optional)": "(opcjonalnie)",
    # -- enroll page
    "1. User": "1. Użytkownik",
    "2. Security key": "2. Klucz bezpieczeństwa",
    "3. Enrollment options": "3. Opcje rejestracji",
    "Profile": "Profil",
    "Key display name": "Nazwa wyświetlana klucza",
    "e.g. YubiKey 5 NFC": "np. YubiKey 5 NFC",
    "Enroll security key": "Zarejestruj klucz",
    "No security key detected": "Nie wykryto klucza bezpieczeństwa",
    "Insert a security key or place it on the NFC reader.": (
        "Włóż klucz bezpieczeństwa lub połóż go na czytniku NFC."
    ),
    "PIN is set": "PIN ustawiony",
    "No PIN set": "Brak PIN-u",
    "minimum PIN length {length}": "minimalna długość PIN-u: {length}",
    "always UV enabled": "włączone „zawsze wymagaj UV”",
    "Enterprise Attestation enabled": "włączona atestacja Enterprise",
    "PIN change required": "wymagana zmiana PIN-u",
    "no support for advanced options": "brak obsługi opcji zaawansowanych",
    "Sign in to the identity provider first.": "Najpierw zaloguj się do dostawcy tożsamości.",
    "No user": "Nie wybrano użytkownika",
    "Search for a user and select one from the list.": (
        "Wyszukaj użytkownika i wybierz go z listy."
    ),
    "No security key": "Brak klucza",
    "Confirm enrollment": "Potwierdź rejestrację",
    "User: {user}": "Użytkownik: {user}",
    "Security key: {key}": "Klucz bezpieczeństwa: {key}",
    "The key will be factory reset. All FIDO credentials on it will be erased.": (
        "Klucz zostanie przywrócony do ustawień fabrycznych. Wszystkie zapisane na nim "
        "poświadczenia FIDO zostaną usunięte."
    ),
    "Cancelling…": "Anulowanie…",
    "Enrollment failed": "Rejestracja nie powiodła się",
    # -- profile options
    "Factory reset the security key": "Przywróć klucz do ustawień fabrycznych",
    "Erases all FIDO credentials and the PIN on the key.": (
        "Usuwa z klucza wszystkie poświadczenia FIDO oraz PIN."
    ),
    "Set new random PIN": "Ustaw nowy losowy PIN",
    "Random PIN length": "Długość losowego PIN-u",
    "Minimum PIN length": "Minimalna długość PIN-u",
    "Force PIN change before use": "Wymuś zmianę PIN-u przed pierwszym użyciem",
    "Require always UV": "Zawsze wymagaj weryfikacji użytkownika (UV)",
    "The key asks for the PIN on every use.": "Klucz wymaga PIN-u przy każdym użyciu.",
    "Require Enterprise Attestation": "Wymagaj atestacji Enterprise",
    # -- profiles page
    "New profile": "Nowy profil",
    "Profile name": "Nazwa profilu",
    "Profile settings": "Ustawienia profilu",
    "Delete profile": "Usuń profil",
    "Delete profile '{name}'?": "Usunąć profil „{name}”?",
    "A profile with this name already exists.": "Profil o tej nazwie już istnieje.",
    "Profile name cannot be empty.": "Nazwa profilu nie może być pusta.",
    "Minimum PIN length must be between 4 and 63.": (
        "Minimalna długość PIN-u musi mieścić się w zakresie 4–63."
    ),
    "Random PIN length must be between 4 and 63.": (
        "Długość losowego PIN-u musi mieścić się w zakresie 4–63."
    ),
    "Random PIN length cannot be shorter than the minimum PIN length.": (
        "Losowy PIN nie może być krótszy niż minimalna długość PIN-u."
    ),
    # -- credentials page
    "FIDO credentials of the selected user": "Poświadczenia FIDO wybranego użytkownika",
    "Delete selected": "Usuń zaznaczone",
    "Delete credential": "Usuń poświadczenie",
    "Delete credential '{name}' of {user}? The user will no longer be able to sign in "
    "with this key.": (
        "Usunąć poświadczenie „{name}” użytkownika {user}? Użytkownik nie będzie mógł "
        "już logować się tym kluczem."
    ),
    "{provider} does not offer an API for listing or deleting credentials. Manage them "
    "in the provider's admin console.": (
        "{provider} nie udostępnia API do listowania ani usuwania poświadczeń. "
        "Zarządzaj nimi w konsoli administracyjnej dostawcy."
    ),
    # -- instances page and dialog
    "Identity provider instances": "Instancje dostawców tożsamości",
    "Each instance is one tenant of an identity provider. Add as many as you need and "
    "switch between them with the selector at the top.": (
        "Każda instancja to jeden tenant dostawcy tożsamości. Dodaj ich tyle, ile "
        "potrzebujesz, i przełączaj się między nimi listą u góry okna."
    ),
    "Add instance": "Dodaj instancję",
    "Edit instance": "Edytuj instancję",
    "Set as active": "Ustaw jako aktywną",
    "Delete instance": "Usuń instancję",
    "Delete instance '{name}' and its saved sign-in?": (
        "Usunąć instancję „{name}” wraz z zapisanym logowaniem?"
    ),
    "Session": "Sesja",
    "Instance name": "Nazwa instancji",
    "e.g. Production tenant": "np. Tenant produkcyjny",
    "Identity provider": "Dostawca tożsamości",
    "Default profile": "Profil domyślny",
    "Use the values of the application registered for YubiEnroll at the identity "
    "provider. The redirect URI must match the registration exactly.": (
        "Użyj wartości aplikacji zarejestrowanej dla YubiEnroll u dostawcy tożsamości. "
        "Redirect URI musi dokładnie odpowiadać temu z rejestracji."
    ),
    "Instance name cannot be empty.": "Nazwa instancji nie może być pusta.",
    "An instance with this name already exists.": "Instancja o tej nazwie już istnieje.",
    "Required field is empty: {field}": "Wymagane pole jest puste: {field}",
    "The redirect URI must start with http://localhost.": (
        "Redirect URI musi zaczynać się od http://localhost."
    ),
    "Settings": "Ustawienia",
    "Language": "Język",
    # -- provider settings
    "Directory (tenant) ID": "Identyfikator katalogu (tenant ID)",
    "Application (client) ID": "Identyfikator aplikacji (client ID)",
    "Client ID": "Client ID",
    "Redirect URI": "Redirect URI",
    "Entra ID endpoint": "Punkt końcowy Entra ID",
    "Microsoft Graph endpoint": "Punkt końcowy Microsoft Graph",
    "Change only for national cloud deployments.": (
        "Zmień tylko dla chmur krajowych (national cloud)."
    ),
    "Okta domain": "Domena Okta",
    "FIDO2 credentials are registered per domain (default or custom).": (
        "Poświadczenia FIDO2 są rejestrowane osobno dla każdej domeny (domyślnej lub własnej)."
    ),
    "Environment ID": "Environment ID",
    "Region": "Region",
    "Custom domain": "Własna domena",
    "MFA policy ID": "ID polityki MFA",
    "Only if the environment uses a custom domain.": (
        "Tylko jeśli środowisko korzysta z własnej domeny."
    ),
    "Leave empty to use the default MFA policy.": (
        "Zostaw puste, aby użyć domyślnej polityki MFA."
    ),
    "Tenant": "Tenant",
    "Realm": "Realm",
    "Journey name": "Nazwa journey",
    "WebAuthn origin": "Origin WebAuthn",
    "The WebAuthn registration journey created for YubiEnroll.": (
        "Journey rejestracji WebAuthn utworzona dla YubiEnroll."
    ),
    "Leave empty to use the tenant address.": "Zostaw puste, aby użyć adresu tenanta.",
    # -- PIN dialogs
    "Security key PIN": "PIN klucza bezpieczeństwa",
    "Enter the current PIN of the security key:": "Podaj obecny PIN klucza bezpieczeństwa:",
    "Wrong PIN.": "Błędny PIN.",
    "Attempts remaining: {retries}": "Pozostało prób: {retries}",
    "Show PIN": "Pokaż PIN",
    "New PIN": "Nowy PIN",
    "Repeat PIN": "Powtórz PIN",
    "Choose a PIN of at least {length} characters.": (
        "Wybierz PIN o długości co najmniej {length} znaków."
    ),
    "The PIN is too short.": "PIN jest za krótki.",
    "The PINs do not match.": "Podane PIN-y nie są takie same.",
    "The security key rejected this PIN (too short or too simple).": (
        "Klucz odrzucił ten PIN (za krótki lub zbyt prosty)."
    ),
    # -- result dialog
    "Enrollment complete": "Rejestracja zakończona",
    "The security key has been enrolled.": "Klucz bezpieczeństwa został zarejestrowany.",
    "Serial number": "Numer seryjny",
    "Temporary PIN:": "Tymczasowy PIN:",
    "The PIN you entered has been set on the key.": "Podany przez Ciebie PIN został ustawiony na kluczu.",
    "The PIN of the key was not changed.": "PIN klucza nie został zmieniony.",
    "The user must change the PIN before first use.": (
        "Użytkownik musi zmienić PIN przed pierwszym użyciem."
    ),
    # -- enrollment engine: progress
    "Checking sign-in and permissions…": "Sprawdzanie logowania i uprawnień…",
    "Factory reset: remove the security key now…": "Reset fabryczny: wyjmij teraz klucz…",
    "Factory reset: insert the security key again…": "Reset fabryczny: włóż klucz ponownie…",
    "Factory reset: touch the security key to confirm…": (
        "Reset fabryczny: dotknij klucza, aby potwierdzić…"
    ),
    "The security key has been reset.": "Klucz został przywrócony do ustawień fabrycznych.",
    "Setting the PIN…": "Ustawianie PIN-u…",
    "Changing the PIN…": "Zmiana PIN-u…",
    "Setting the minimum PIN length to {length}…": (
        "Ustawianie minimalnej długości PIN-u na {length}…"
    ),
    "Enabling 'Require always UV'…": "Włączanie „zawsze wymagaj UV”…",
    "Enabling Enterprise Attestation…": "Włączanie atestacji Enterprise…",
    "Requesting a registration challenge…": "Pobieranie wyzwania rejestracji…",
    "Touch the security key to create the credential…": (
        "Dotknij klucza, aby utworzyć poświadczenie…"
    ),
    "Registering the credential with the identity provider…": (
        "Rejestrowanie poświadczenia u dostawcy tożsamości…"
    ),
    "Forcing a PIN change before first use…": "Wymuszanie zmiany PIN-u przed pierwszym użyciem…",
    "Done.": "Gotowe.",
    # -- enrollment engine: errors
    "Enrollment cancelled.": "Rejestracja anulowana.",
    "No security key detected. Insert a key and try again.": (
        "Nie wykryto klucza bezpieczeństwa. Włóż klucz i spróbuj ponownie."
    ),
    "The selected security key is no longer connected. Refresh the list.": (
        "Wybrany klucz nie jest już podłączony. Odśwież listę."
    ),
    "Timed out waiting for the security key.": "Upłynął czas oczekiwania na klucz.",
    "The key was not touched in time.": "Klucz nie został dotknięty na czas.",
    "This security key does not support FIDO2.": "Ten klucz nie obsługuje FIDO2.",
    "This security key does not support a PIN.": "Ten klucz nie obsługuje PIN-u.",
    "This security key does not support 'Require always UV' (firmware 5.5+ needed).": (
        "Ten klucz nie obsługuje opcji „zawsze wymagaj UV” (wymagany firmware 5.5+)."
    ),
    "This security key does not support Enterprise Attestation.": (
        "Ten klucz nie obsługuje atestacji Enterprise."
    ),
    "This security key cannot enforce a minimum PIN length or a forced PIN change "
    "(firmware 5.5+ needed).": (
        "Ten klucz nie potrafi wymusić minimalnej długości PIN-u ani zmiany PIN-u "
        "(wymagany firmware 5.5+)."
    ),
    "The reset was not accepted. It must be confirmed within a few seconds of inserting "
    "the key.": (
        "Reset nie został przyjęty. Trzeba go potwierdzić w ciągu kilku sekund od "
        "włożenia klucza."
    ),
    "Factory reset failed.": "Reset fabryczny nie powiódł się.",
    "The current PIN is shorter than the minimum PIN length of the profile. Enable 'Set "
    "new random PIN' or 'Factory reset'.": (
        "Obecny PIN jest krótszy niż minimalna długość PIN-u w profilu. Włącz opcję "
        "„Ustaw nowy losowy PIN” lub reset fabryczny."
    ),
    "Too many wrong PIN attempts. Re-insert the key and try again.": (
        "Zbyt wiele błędnych prób PIN-u. Włóż klucz ponownie i spróbuj jeszcze raz."
    ),
    "The PIN is blocked. The key must be factory reset.": (
        "PIN jest zablokowany. Klucz trzeba przywrócić do ustawień fabrycznych."
    ),
    "This security key is already registered for this user.": (
        "Ten klucz jest już zarejestrowany dla tego użytkownika."
    ),
    "The identity provider returned an RP ID that does not match its origin.": (
        "Dostawca tożsamości zwrócił RP ID niezgodne z jego adresem (origin)."
    ),
    "The security key reported an error: {detail}": "Klucz zgłosił błąd: {detail}",
    "The credential was registered, but forcing a PIN change failed: {detail}": (
        "Poświadczenie zostało zarejestrowane, ale nie udało się wymusić zmiany PIN-u: {detail}"
    ),
    # -- bulk enrollment
    "Bulk enrollment": "Wdrożenie masowe",
    "User list": "Lista użytkowników",
    "Text or CSV file with one user per line: user name, login or e-mail. In a CSV with "
    "several columns, name the user column 'username'.": (
        "Plik tekstowy lub CSV, jeden użytkownik w wierszu: nazwa użytkownika, login lub "
        "e-mail. W pliku CSV z wieloma kolumnami nazwij kolumnę użytkownika „username”."
    ),
    "Load from file…": "Wczytaj z pliku…",
    "Load user list": "Wczytaj listę użytkowników",
    "User lists (*.csv *.txt);;All files (*)": (
        "Listy użytkowników (*.csv *.txt);;Wszystkie pliki (*)"
    ),
    "No users were found in this file.": "W tym pliku nie znaleziono żadnych użytkowników.",
    "Clear list": "Wyczyść listę",
    "Looking up users in the directory…": "Wyszukiwanie użytkowników w katalogu…",
    "Load a user list to begin.": "Wczytaj listę użytkowników, aby rozpocząć.",
    "Ready. Insert the first security key and press Start.": (
        "Gotowe. Włóż pierwszy klucz i naciśnij Start."
    ),
    "This list belongs to another instance. Export the results and clear it.": (
        "Ta lista należy do innej instancji. Wyeksportuj wyniki i wyczyść ją."
    ),
    "Enrollment options": "Opcje rejestracji",
    "Add the serial number to the key name": "Dodaj numer seryjny do nazwy klucza",
    "Show PINs in the list": "Pokaż PIN-y na liście",
    "Start": "Start",
    "Stop": "Zatrzymaj",
    "Retry failed": "Ponów nieudane",
    "Export results…": "Eksportuj wyniki…",
    "Export results": "Eksport wyników",
    "Export": "Eksportuj",
    "The file will contain the temporary PINs in plain text. Store it securely and delete "
    "it once the keys have been handed out.": (
        "Plik będzie zawierał tymczasowe PIN-y zapisane jawnym tekstem. Przechowuj go "
        "bezpiecznie i usuń po wydaniu kluczy."
    ),
    "Results exported to {path}": "Wyniki wyeksportowano do {path}",
    "Unsaved PINs": "Niezapisane PIN-y",
    "The temporary PINs have not been exported and will be lost. Continue?": (
        "Tymczasowe PIN-y nie zostały wyeksportowane i zostaną utracone. Kontynuować?"
    ),
    "Start bulk enrollment": "Rozpocznij wdrożenie masowe",
    "{count} security key(s) will be enrolled, one per user.": (
        "Liczba kluczy do zarejestrowania: {count} (jeden na użytkownika)."
    ),
    "Every inserted key will be factory reset. All FIDO credentials on it will be erased.": (
        "Każdy włożony klucz zostanie przywrócony do ustawień fabrycznych. Wszystkie "
        "zapisane na nim poświadczenia FIDO zostaną usunięte."
    ),
    "Bulk enrollment paused": "Wdrożenie masowe wstrzymane",
    "{count} ready": "gotowych: {count}",
    "{count} enrolled": "zarejestrowanych: {count}",
    "{count} failed": "nieudanych: {count}",
    "{count} not found": "nie znaleziono: {count}",
    "Checking…": "Sprawdzanie…",
    "Ready": "Gotowy",
    "Not found": "Nie znaleziono",
    "In progress": "W toku",
    "Enrolled": "Zarejestrowano",
    "Failed": "Niepowodzenie",
    "Status": "Status",
    "Key name": "Nazwa klucza",
    "Temporary PIN": "Tymczasowy PIN",
    "Enrolled at": "Data rejestracji",
    "Message": "Komunikat",
    "Insert the security key for {user}…": "Włóż klucz dla użytkownika {user}…",
    "Remove the previous key, then insert the key for {user}…": (
        "Wyjmij poprzedni klucz, a następnie włóż klucz dla użytkownika {user}…"
    ),
    "Several security keys are connected. Leave only one connected.": (
        "Podłączono kilka kluczy. Zostaw podłączony tylko jeden."
    ),
    "Batch finished.": "Wdrożenie zakończone.",
    "Security key {serial} was already enrolled in this batch.": (
        "Klucz {serial} został już zarejestrowany w tym wdrożeniu."
    ),
    # -- key details and naming
    "Firmware": "Firmware",
    "Ready to enroll.": "Gotowe do rejestracji.",
    "serial number not readable": "nie można odczytać numeru seryjnego",
    "Key will be registered as: {name}": "Klucz zostanie zarejestrowany jako: {name}",
    "Key name: {name}": "Nazwa klucza: {name}",
    # -- profile summary
    "factory reset": "reset fabryczny",
    "no factory reset": "bez resetu fabrycznego",
    "random PIN of {length} digits": "losowy PIN ({length} cyfr)",
    "PIN entered by the operator": "PIN podawany przez operatora",
    "forced PIN change": "wymuszona zmiana PIN-u",
    "always UV": "zawsze wymagaj UV",
    "Enterprise Attestation": "atestacja Enterprise",
    # -- appearance
    "Appearance": "Wygląd",
    "Light": "Jasny",
    "Dark": "Ciemny",
    "Custom": "Własny",
    "Custom colours": "Własne kolory",
    "Accent colour…": "Kolor akcentu…",
    "Choose the accent colour": "Wybierz kolor akcentu",
    "Restart the application to apply the change.": (
        "Uruchom aplikację ponownie, aby zastosować zmianę."
    ),
    "Version {version}": "Wersja {version}",
    # -- hand-over to the user
    "Pass it on to the user": "Przekaż użytkownikowi",
    "The message contains the PIN. Send it through a different channel than the key "
    "itself.": (
        "Wiadomość zawiera PIN. Wyślij ją innym kanałem niż sam klucz."
    ),
    "Copy PIN": "Kopiuj PIN",
    "Copy message": "Kopiuj wiadomość",
    "E-mail draft…": "Szkic e-maila…",
    "Save to file…": "Zapisz do pliku…",
    "Save message": "Zapisz wiadomość",
    "Text files (*.txt)": "Pliki tekstowe (*.txt)",
    "Copied. The clipboard will be cleared in one minute.": (
        "Skopiowano. Schowek zostanie wyczyszczony za minutę."
    ),
    "Saved to {path}. The file contains the PIN.": "Zapisano w {path}. Plik zawiera PIN.",
    "The PIN is not stored anywhere. It is shown only in this window.": (
        "PIN nie jest nigdzie zapisywany. Widać go tylko w tym oknie."
    ),
    "No e-mail address is known for this user.": "Brak adresu e-mail tego użytkownika.",
    "A draft was opened in your e-mail program. Review it and send it.": (
        "W programie pocztowym otwarto szkic wiadomości. Sprawdź go i wyślij."
    ),
    "No e-mail program is available. Copy the message instead.": (
        "Brak programu pocztowego. Skopiuj wiadomość."
    ),
    "security key": "klucz bezpieczeństwa",
    "(provided separately)": "(przekazany osobno)",
    "You will be asked to set your own PIN the first time you use the key.": (
        "Przy pierwszym użyciu klucza pojawi się prośba o ustawienie własnego PIN-u."
    ),
    "Message for the user…": "Wiadomość dla użytkownika…",
    "Select an enrolled user to copy, e-mail or save the hand-over message.": (
        "Zaznacz zarejestrowanego użytkownika, aby skopiować, wysłać lub zapisać wiadomość."
    ),
    # -- export options
    "CSV files (*.csv)": "Pliki CSV (*.csv)",
    "Enrolled users only": "Tylko zarejestrowani użytkownicy",
    "All users on the list, with their status": "Wszyscy użytkownicy z listy, ze statusem",
    "Include temporary PINs": "Dołącz tymczasowe PIN-y",
    "CSV, semicolon separated": "CSV rozdzielany średnikami",
    "CSV, comma separated": "CSV rozdzielany przecinkami",
    "Format": "Format",
    # -- settings page
    "Colour scheme": "Kolorystyka",
    "Same as the system (light or dark)": "Zgodna z systemem (jasna lub ciemna)",
    "Same as the system": "Zgodny z systemem",
    "Message for the user": "Wiadomość dla użytkownika",
    "Used after an enrollment for the e-mail draft, the copied message and the saved "
    "file. Placeholders: {placeholders}.": (
        "Używana po rejestracji w szkicu e-maila, kopiowanej wiadomości i zapisywanym "
        "pliku. Pola do podstawienia: {placeholders}."
    ),
    "Subject": "Temat",
    "Text": "Treść",
    "Restore the default text": "Przywróć tekst domyślny",
    "Saved.": "Zapisano.",
    "The default text has been restored.": "Przywrócono tekst domyślny.",
    "About": "O programie",
    "Version": "Wersja",
    "License": "Licencja",
    "Project page": "Strona projektu",
    "Documentation": "Dokumentacja",
    "KeyEnroll is an independent open-source project. It is not affiliated with or "
    "endorsed by Yubico, Microsoft, Okta or Ping Identity.": (
        "KeyEnroll jest niezależnym projektem open source. Nie jest powiązany z firmami "
        "Yubico, Microsoft, Okta ani Ping Identity, ani przez nie wspierany."
    ),
    "Open the folder with settings and logs": "Otwórz folder z ustawieniami i logami",
    # -- unexpected errors
    "An unexpected error occurred:": "Wystąpił nieoczekiwany błąd:",
    "Details were written to the log: {path}": "Szczegóły zapisano w logu: {path}",
    "The settings file could not be read and was set aside as {path}. KeyEnroll started "
    "with default settings.": (
        "Nie udało się odczytać pliku ustawień; odłożono go jako {path}. KeyEnroll "
        "uruchomił się z ustawieniami domyślnymi."
    ),
    # -- updates
    "Check for updates": "Sprawdź aktualizacje",
    "Checking for updates…": "Sprawdzanie aktualizacji…",
    "Open the download page": "Otwórz stronę pobierania",
    "Version {latest} is available (you have {current}).": (
        "Dostępna jest wersja {latest} (masz {current})."
    ),
    "You have the latest version ({current}).": "Masz najnowszą wersję ({current}).",
    "Could not reach the update server. Check the connection.": (
        "Nie udało się połączyć z serwerem aktualizacji. Sprawdź połączenie."
    ),
    "No published release was found.": "Nie znaleziono opublikowanego wydania.",
    "The update server is busy. Try again in a few minutes.": (
        "Serwer aktualizacji jest zajęty. Spróbuj ponownie za kilka minut."
    ),
    "The update server returned an unexpected answer.": (
        "Serwer aktualizacji zwrócił nieoczekiwaną odpowiedź."
    ),
}
