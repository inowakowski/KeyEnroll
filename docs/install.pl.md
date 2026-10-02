# Instalacja

Instalatory dla każdej platformy są dołączone do każdego wydania na GitHubie.

[Otwórz stronę pobierania](https://github.com/inowakowski/KeyEnroll/releases/latest){ .md-button .md-button--primary }

| System operacyjny | Plik do pobrania |
|---|---|
| Windows 10/11, procesor Intel lub AMD | `KeyEnroll-<wersja>-windows-x64-setup.exe` |
| Windows 11 na ARM | `KeyEnroll-<wersja>-windows-arm64-setup.exe` |
| macOS, Apple Silicon (M1 i nowsze) | `KeyEnroll-<wersja>-macos-arm64.dmg` |
| macOS, Intel | `KeyEnroll-<wersja>-macos-x64.dmg` |
| Debian, Ubuntu i pochodne | `keyenroll_<wersja>_amd64.deb` lub `keyenroll_<wersja>_arm64.deb` |
| Inne dystrybucje Linuksa | `KeyEnroll-<wersja>-linux-x64.tar.gz` lub `…-linux-arm64.tar.gz` |

!!! warning "Paczki nie są podpisane cyfrowo"
    Certyfikaty do podpisywania kodu kosztują, a to projekt darmowy. Dlatego Windows
    SmartScreen i macOS Gatekeeper pokazują ostrzeżenie przy pierwszym uruchomieniu.
    Poniżej opisano, jak je ominąć. Rób to wyłącznie dla pliku pobranego ze strony
    wydań tego projektu.

## Windows { #windows }

1. Uruchom plik `…-setup.exe`. Jeśli SmartScreen pokaże komunikat *System Windows
   ochronił ten komputer*, wybierz **Więcej informacji**, a potem **Uruchom mimo to**.
2. Przejdź przez instalator. Wymaga on uprawnień administratora i proponuje skrót
   na pulpicie.
3. Uruchom KeyEnroll z menu Start. Windows poprosi o uprawnienia administratora
   (okno UAC) **przy każdym uruchomieniu aplikacji**.

!!! info "Po co uprawnienia administratora?"
    Windows pozwala na bezpośredni dostęp do kluczy FIDO tylko procesom z podniesionymi
    uprawnieniami. Bez nich aplikacja się uruchomi, ale nie zobaczy żadnego klucza;
    pojawi się wtedy żółty pasek z przyciskiem **Uruchom jako administrator**.

Aplikację usuniesz w *Ustawienia → Aplikacje → Zainstalowane aplikacje*. Twoje
ustawienia pozostają na dysku, patrz [Dane i bezpieczeństwo](data.md).

## macOS

1. Otwórz plik `.dmg` i przeciągnij **KeyEnroll** na folder **Applications**.
2. Uruchom aplikację z folderu Aplikacje. macOS odmówi pierwszego uruchomienia,
   bo aplikacja nie jest notaryzowana. Otwórz *Ustawienia systemowe → Prywatność
   i ochrona*, przewiń do komunikatu o KeyEnroll i wybierz **Otwórz mimo to**.
   W starszych wersjach macOS wystarczy kliknąć aplikację prawym przyciskiem
   i wybrać **Otwórz**.

Uprawnienia administratora nie są potrzebne. Logowanie do dostawcy tożsamości jest
przechowywane w Pęku kluczy macOS; system może za pierwszym razem zapytać o zgodę.

## Linux

=== "Debian / Ubuntu"

    ```bash
    sudo apt install ./keyenroll_<wersja>_amd64.deb
    ```

    Instaluje to także zalecane pakiety dla kluczy bezpieczeństwa i czytników NFC.
    Uruchom **KeyEnroll** z menu aplikacji albo poleceniem `keyenroll`.

=== "Inne dystrybucje"

    ```bash
    tar -xzf KeyEnroll-<wersja>-linux-x64.tar.gz
    ```

    ```bash
    ./KeyEnroll/KeyEnroll
    ```

Linux wymaga trzech rzeczy, których instalator nie zagwarantuje w każdej dystrybucji:

| Wymaganie | Po co | Jak |
|---|---|---|
| Reguły udev dla kluczy FIDO | Bez nich klucz może otworzyć tylko root. | Są w większości współczesnych dystrybucji (systemd 252 lub nowszy). W innym razie zainstaluj `libu2f-udev` lub `libfido2`. |
| Secret Service (GNOME Keyring, KWallet) | Przechowuje logowanie. Bez niego trzeba logować się po każdym uruchomieniu aplikacji. | Część środowisk GNOME i KDE. |
| `pcscd` | Tylko dla kluczy używanych przez czytnik NFC. | `sudo apt install pcscd` |

## Aktualizacje

*Ustawienia → O programie → Sprawdź aktualizacje* pyta GitHuba o najnowsze
opublikowane wydanie. Jeśli jest nowsze, pojawia się przycisk otwierający stronę
pobierania. KeyEnroll niczego sam nie pobiera ani nie instaluje i nie sprawdza
aktualizacji w tle.

Aby zaktualizować, zainstaluj nową wersję na starą. Ustawienia, instancje i profile
zostają zachowane.

## Uruchamianie ze źródeł

Programiści mogą uruchomić aplikację bezpośrednio; opis jest w pliku
[README](https://github.com/inowakowski/KeyEnroll#praca-ze-źródłami) w repozytorium.

## Opcje uruchamiania { #start-up-options }

Zainstalowana aplikacja przyjmuje kilka opcji wiersza poleceń, przydatnych, gdy
potrzebny jest szczegółowy log:

| Opcja | Znaczenie |
|---|---|
| `-l DEBUG`, `--log-level DEBUG` | Bardziej szczegółowy log (`ERROR`, `WARNING`, `INFO`, `DEBUG`). |
| `--log-file <ścieżka>` | Zapisuje log do wskazanego pliku zamiast w domyślnym miejscu. |
| `-v`, `--version` | Wypisuje wersję i kończy działanie. |
