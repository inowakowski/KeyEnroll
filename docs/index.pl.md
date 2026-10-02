# KeyEnroll

KeyEnroll to aplikacja do **rejestrowania kluczy bezpieczeństwa FIDO2 (YubiKey)
w imieniu użytkowników**. Administrator wkłada klucz, wybiera użytkownika, a aplikacja
przygotowuje klucz i rejestruje go u dostawcy tożsamości — użytkownik dostaje klucz,
który od razu działa.

Działa na **Windows (x64 i ARM64), macOS i Linuksie**, jest darmowa i ma otwarty kod
(licencja MIT).

[Pobierz najnowszą wersję](https://github.com/inowakowski/KeyEnroll/releases/latest){ .md-button .md-button--primary }
[Szybki start](quickstart.md){ .md-button }

![Strona Rejestracja](assets/screenshots/pl/enroll.png){ .shot }

## Co potrafi

| Funkcja | Co to oznacza |
|---|---|
| **Czterej dostawcy tożsamości** | Microsoft Entra ID, Okta, PingOne PingID i PingOne Advanced Identity Cloud. |
| **Kilka tenantów w jednej aplikacji** | Dodaj tyle [instancji](instances.md), ile potrzebujesz, i przełączaj się między nimi listą u góry okna. Każda ma własne logowanie. |
| **Przygotowanie klucza** | Reset fabryczny, losowy tymczasowy PIN, minimalna długość PIN-u, wymuszenie zmiany PIN-u, „zawsze wymagaj weryfikacji użytkownika”, atestacja Enterprise. Zapisywane jako [profile](profiles.md) do ponownego użycia. |
| **Wdrożenie masowe** | Wczytaj [listę użytkowników z pliku](bulk.md), rejestruj klucz po kluczu i wyeksportuj wynik razem z tymczasowymi PIN-ami. |
| **Przekazanie klucza użytkownikowi** | Po rejestracji [skopiuj gotową wiadomość, otwórz szkic e-maila albo zapisz plik](enroll.md#handing-the-key-over) z PIN-em i numerem seryjnym. |
| **Przegląd poświadczeń** | [Lista i usuwanie](credentials.md) kluczy zarejestrowanych dla użytkownika. |
| **Sześć języków** | Polski, angielski, niemiecki, hiszpański, francuski i włoski. |

## Od czego zacząć

<div class="grid cards" markdown>

- **[Instalacja](install.md)**  
  Pobieranie, wymagania i pierwsze uruchomienie w każdym systemie.
- **[Szybki start](quickstart.md)**  
  Od pustej aplikacji do pierwszego zarejestrowanego klucza w pięciu krokach.
- **[Okno aplikacji w skrócie](interface.md)**  
  Do czego służy każda część okna.
- **[Dostawcy tożsamości](providers.md)**  
  Co trzeba skonfigurować w Entra ID, Okta i PingOne przed pierwszym logowaniem.

</div>

## KeyEnroll a YubiEnroll

Yubico udostępnia narzędzie wiersza poleceń YubiEnroll, dostępne tylko dla Windows.
KeyEnroll **nie jest nakładką na to narzędzie**. Ma własny silnik: z kluczem rozmawia
przez otwartą bibliotekę [python-fido2](https://github.com/Yubico/python-fido2),
a z dostawcami tożsamości przez ich publiczne API. Korzysta z tych samych rejestracji
aplikacji u dostawcy, które opisuje
[dokumentacja YubiEnroll](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html),
więc tenant przygotowany dla YubiEnroll działa także z KeyEnroll.

!!! note "Projekt niezależny"
    KeyEnroll nie jest powiązany z firmami Yubico, Microsoft, Okta ani Ping Identity,
    ani przez nie wspierany. YubiKey i YubiEnroll są znakami towarowymi Yubico AB;
    pozostałe nazwy należą do ich właścicieli i służą wyłącznie opisaniu zgodności.

## Co zostało sprawdzone { #what-has-been-tested }

KeyEnroll to młody program. Zanim zaczniesz na nim polegać, sprawdź, co jest
potwierdzone:

- Rejestracja w **Okta kluczem USB na Windows ARM64** została potwierdzona na
  prawdziwym sprzęcie.
- Cała reszta — Entra ID, PingOne, PingOne AIC, wdrożenie masowe oraz paczki dla
  macOS, Linuksa i Windows x64 — jest objęta testami automatycznymi na programowym
  kluczu i symulowanych odpowiedziach dostawców, ale **nie została jeszcze
  potwierdzona na żywym tenancie z fizycznym kluczem**.

Najpierw wypróbuj aplikację z zapasowym kluczem i kontem testowym, a o wynikach
[daj znać](https://github.com/inowakowski/KeyEnroll/issues).
