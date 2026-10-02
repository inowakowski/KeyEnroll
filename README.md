# KeyEnroll

Graficzna aplikacja do rejestrowania kluczy FIDO2 (YubiKey) w imieniu użytkowników —
otwartoźródłowy odpowiednik `yubienroll` CLI firmy Yubico, działający na Windows
(x64 i ARM64), macOS i Linuksie. Licencja: [MIT](LICENSE).

> KeyEnroll jest niezależnym projektem. Nie jest powiązany z Yubico, Microsoftem, Oktą
> ani Ping Identity, ani przez nie wspierany. YubiKey i YubiEnroll są znakami towarowymi
> Yubico AB; pozostałe nazwy należą do ich właścicieli i służą wyłącznie opisaniu
> zgodności.

**To nie jest nakładka na YubiEnroll CLI** (CLI istnieje tylko na Windows i ma zamknięty
kod). Aplikacja ma własny silnik: z kluczem rozmawia przez
bibliotekę [python-fido2](https://github.com/Yubico/python-fido2), a z dostawcami
tożsamości przez ich publiczne API. Używa tych samych rejestracji aplikacji u dostawcy,
które opisuje [dokumentacja YubiEnroll](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html).

## Funkcje

- Microsoft Entra ID, Okta, PingOne PingID, PingOne Advanced Identity Cloud.
- Dowolna liczba instancji (tenantów) w jednej aplikacji, przełączanych listą u góry okna;
  każda ma własne logowanie i profil domyślny.
- Profile rejestracji: reset fabryczny, losowy PIN, minimalna długość PIN-u, wymuszenie
  zmiany PIN-u, „zawsze wymagaj UV”, atestacja Enterprise.
- Numer seryjny klucza widoczny przy rejestracji; opcjonalnie dopisywany do nazwy klucza.
- **Wdrożenie masowe**: lista użytkowników z pliku, rejestracja klucz po kluczu,
  eksport numerów seryjnych i tymczasowych PIN-ów do CSV.
- Lista i usuwanie poświadczeń użytkownika (Entra, Okta, PingOne).
- Kolorystyka do wyboru: jasna, ciemna, Yubico albo własna (jasna lub ciemna baza
  i dowolny kolor akcentu), zmieniana na żywo w *Instancje → Ustawienia*.
- Język polski i angielski.

## Instalacja

Instalatory dla każdej platformy powstają w GitHub Actions (patrz „Wydawanie wersji”):

| System | Plik |
|---|---|
| Windows x64 / ARM64 | `KeyEnroll-<wersja>-windows-<arch>-setup.exe` |
| macOS (Apple Silicon / Intel) | `KeyEnroll-<wersja>-macos-<arch>.dmg` |
| Debian / Ubuntu | `keyenroll_<wersja>_<arch>.deb` |
| Inne dystrybucje Linuksa | `KeyEnroll-<wersja>-linux-<arch>.tar.gz` |

Paczki **nie są podpisane cyfrowo**. Windows SmartScreen i macOS Gatekeeper pokażą
ostrzeżenie przy pierwszym uruchomieniu; usunięcie go wymaga certyfikatu do podpisywania
kodu (Windows) i konta Apple Developer z notaryzacją (macOS).

### Wymagania systemowe

| System | Uwagi |
|---|---|
| Windows 10/11 | Aplikacja działa **jako administrator** — Windows nie daje zwykłym procesom bezpośredniego dostępu do kluczy FIDO. Zainstalowana wersja sama prosi o podniesienie uprawnień. |
| macOS | Nie wymaga uprawnień administratora. |
| Linux | Potrzebne reguły udev dla kluczy FIDO (pakiet `libu2f-udev` / `libfido2` lub systemd ≥ 252). Dla NFC: `pcscd`. Tokeny logowania trafiają do Secret Service (GNOME Keyring/KWallet); bez niego logowanie nie przetrwa restartu aplikacji. |

## Jak używać

1. **Instancje** → *Dodaj instancję*: wybierz dostawcę i wpisz wartości z rejestracji
   aplikacji. Tu także zmienisz język i motyw.
2. **Zaloguj** (prawy górny róg) — otworzy się przeglądarka.
3. **Profile** — zestawy opcji rejestracji (domyślne wartości jak w YubiEnroll CLI).
4. **Rejestracja** — wyszukaj użytkownika, wybierz klucz (widać jego numer seryjny
   i firmware), w razie potrzeby zmień opcje tylko dla tej rejestracji i kliknij
   *Zarejestruj klucz*. Na końcu aplikacja pokaże numer seryjny i tymczasowy PIN.
5. **Poświadczenia** — lista i usuwanie kluczy użytkownika.

### Nazwa klucza i numer seryjny

Pole *Nazwa wyświetlana klucza* to nazwa, pod którą poświadczenie zapisze dostawca.
Zaznaczenie *Dodaj numer seryjny do nazwy klucza* dopisuje numer na końcu
(np. `YubiKey 5 NFC 23456789`). Entra ID ogranicza nazwę do 30 znaków — wtedy skracana
jest nazwa, nigdy numer. Okta sama nadaje nazwę na podstawie modelu klucza i ignoruje to
pole. Klucze z serii Security Key nie udostępniają numeru seryjnego.

### Wdrożenie masowe

1. Przygotuj plik `.txt` lub `.csv` z jednym użytkownikiem w wierszu (nazwa użytkownika,
   login lub e-mail). W pliku CSV z wieloma kolumnami nazwij kolumnę użytkownika
   `username` (rozpoznawane są też `login`, `upn`, `userPrincipalName`, `email`).
   Wiersze zaczynające się od `#` są pomijane.
2. **Wdrożenie masowe** → *Wczytaj z pliku*. Aplikacja sprawdzi każdego użytkownika
   w katalogu; nieznalezieni dostaną status „Nie znaleziono” i zostaną pominięci.
3. Wybierz profil i nazwę klucza, kliknij *Start* i wkładaj kolejne klucze, gdy aplikacja
   o to poprosi. Świeżo włożony klucz jest resetowany od razu, bez ponownego wyjmowania.
4. *Eksportuj wyniki* zapisuje CSV: użytkownik, status, numer seryjny, nazwa klucza,
   tymczasowy PIN, data. Na podstawie numeru seryjnego dopasujesz klucz do osoby.

Zabezpieczenia: przed kolejnym użytkownikiem trzeba wyjąć poprzedni klucz, a klucz
o numerze seryjnym już użytym w tym wdrożeniu jest odrzucany przed resetem. Po błędzie
wdrożenie zatrzymuje się; *Ponów nieudane* przywraca wiersze do kolejki.

**Plik z wynikami zawiera PIN-y jawnym tekstem.** Przechowuj go krótko i bezpiecznie.
Losowe PIN-y nigdy nie zaczynają się od zera, żeby arkusz kalkulacyjny ich nie zniekształcił.

### Konfiguracja u dostawców

| Dostawca | Pola | Domyślny redirect URI |
|---|---|---|
| Microsoft Entra ID | Tenant ID, Client ID | `http://localhost/yubienroll-redirect` |
| Okta | domena, Client ID | `http://localhost:8080/yubienroll-redirect` |
| PingOne PingID | Environment ID, Client ID, region, opcjonalnie własna domena i ID polityki MFA | `http://localhost:9443/yubienroll-callback` |
| PingOne AIC | tenant, realm, nazwa journey, Client ID, opcjonalnie origin | `http://localhost:8443/yubienroll-redirect` |

- **Entra ID**: uprawnienia delegowane `User.ReadBasic.All` i
  `UserAuthenticationMethod.ReadWrite.All`; operator potrzebuje roli Authentication
  Administrator. W polityce Passkey (FIDO2) musi być włączone *Allow self-service setup*.
- **PingOne AIC**: w węźle *WebAuthn Registration Node* wyłącz *Return challenge as
  JavaScript*. Listowanie i usuwanie poświadczeń nie jest dostępne.
- Redirect URI musi zaczynać się od `http://localhost` i dokładnie zgadzać się
  z rejestracją (u Okta i Ping łącznie z portem).

## Gdzie są dane

- Konfiguracja: `%APPDATA%\KeyEnroll\config.json`,
  `~/Library/Application Support/KeyEnroll/` lub `~/.config/keyenroll/`.
- Tokeny odświeżania: wyłącznie w systemowym magazynie poświadczeń.
- Tymczasowe PIN-y żyją tylko w pamięci aplikacji, dopóki ich nie wyeksportujesz.

## Stan projektu

- Rejestracja w **Okta kluczem USB na Windows ARM64** została potwierdzona na prawdziwym
  sprzęcie.
- Pozostałe ścieżki sprawdza 135 testów automatycznych na programowym symulatorze klucza
  i spreparowanych odpowiedziach dostawców: Entra ID, PingOne i PingOne AIC oraz tryb
  masowy **nie były jeszcze testowane na żywym tenancie**.
- Instalatory dla macOS i Linuksa oraz workflow GitHub Actions nie były jeszcze uruchamiane.

## Praca ze źródłami

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python -m pip install --only-binary=cryptography -e ".[nfc,dev]"
```

```bash
.venv\Scripts\python -m keyenroll -l DEBUG --log-file log.txt
```

```bash
.venv\Scripts\python -m pytest -q
```

Na macOS/Linuksie zamiast `.venv\Scripts\python` użyj `.venv/bin/python`.

### Budowanie instalatora lokalnie

| System | Polecenie | Wymaga |
|---|---|---|
| Windows | `pwsh packaging\windows\build_installer.ps1` | Inno Setup 6.3+ |
| macOS | `sh packaging/macos/build_dmg.sh` | — |
| Linux | `sh packaging/linux/build_deb.sh` | `dpkg-deb` |

Wynik trafia do `dist/installer/`. Każdą platformę trzeba budować na niej samej.

### Wydawanie wersji

1. Zmień numer wersji w `src/keyenroll/__init__.py` i `pyproject.toml`.
2. Wypchnij tag, np. `v0.2.0`. Workflow `.github/workflows/build.yml` uruchomi testy,
   zbuduje instalatory dla sześciu platform i dołączy je do wydania na GitHubie.

## Licencja

Kod KeyEnroll jest udostępniony na licencji [MIT](LICENSE), © 2026 Ignacy Nowakowski.

Instalatory zawierają biblioteki na własnych licencjach (m.in. Qt/PySide6 na LGPLv3,
python-fido2 na BSD-2-Clause). Ich wykaz jest w [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md),
a pliki licencji dostarczane z bibliotekami trafiają do folderu `licenses/` każdej paczki.
Teksty LGPL-3.0 i GPL-3.0 wymagane przez licencję Qt (paczka Qt ich nie zawiera) leżą
w `packaging/licenses/` — skrypt budujący dołącza do paczki wszystko, co tam znajdzie.

Po zmianie nazwy z „YubiEnroll GUI” aplikacja przy pierwszym uruchomieniu wczytuje
konfigurację ze starego folderu; zalogować się trzeba ponownie.
