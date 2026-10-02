# Dane i bezpieczeństwo

Co KeyEnroll zapisuje, gdzie, i co nigdy nie opuszcza aplikacji.

## Gdzie co jest

| Co | Gdzie | Czy zawiera tajemnice? |
|---|---|---|
| Ustawienia: instancje, profile, wygląd, język, szablon wiadomości, układ okna | `config.json` w folderze ustawień | Nie. Identyfikatory tenanta i klienta to identyfikatory, nie sekrety. |
| Logowanie (token odświeżania) każdej instancji | Systemowy magazyn poświadczeń | Tak — chronione przez system operacyjny, przypisane do Twojego konta. |
| Log | `logs/keyenroll.log` w folderze ustawień | Nie zawiera PIN-ów ani tokenów. |
| Tymczasowe PIN-y | Wyłącznie w pamięci działającej aplikacji | Na dysku są tylko w plikach, które **sam** wyeksportujesz lub zapiszesz. |

Folder ustawień:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\KeyEnroll` |
| macOS | `~/Library/Application Support/KeyEnroll` |
| Linux | `~/.config/keyenroll` |

Otwiera go *Ustawienia → Otwórz folder z ustawieniami i logami*.

Magazyn poświadczeń to Menedżer poświadczeń Windows, Pęk kluczy macOS albo Secret
Service (GNOME Keyring, KWallet) w Linuksie. Jeśli żaden z nich nie jest dostępny,
KeyEnroll nie zapisuje logowania do pliku: po prostu go nie zapamiętuje.

W macOS i Linuksie folder ustawień jest zamknięty dla innych kont na komputerze.
W Windows folder leży w profilu użytkownika, który jest prywatny z założenia.

## PIN-y

- Losowy PIN powstaje na Twoim komputerze, z użyciem systemowego generatora liczb
  losowych przeznaczonego do tajemnic.
- Do klucza jest przesyłany szyfrowanym kanałem określonym przez standard FIDO.
  **Nigdy nie trafia do dostawcy tożsamości** ani nigdzie indziej.
- Jest widoczny w oknie wyniku, a na liście wdrożenia masowego pozostaje do
  wyczyszczenia listy lub zamknięcia aplikacji. Nigdy nie jest zapisywany
  w ustawieniach ani w logu.
- Skopiowany PIN lub wiadomość znika ze schowka po minucie, chyba że w międzyczasie
  skopiowano coś innego. Jest też oznaczany jako sekret — to prośba do historii
  schowka Windows i jej synchronizacji z chmurą, menedżerów schowka w macOS oraz
  Klippera w KDE, żeby go nie zapisywały.
- Pliki, które eksportujesz lub zapisujesz, zawierają PIN jawnym tekstem. W macOS
  i Linuksie może je odczytać tylko Twoje konto, także gdy zastępują starszy plik.
  W Windows dostają uprawnienia folderu, w którym je zapisujesz — wybierz więc
  folder dostępny tylko dla Ciebie. Usuń je po wydaniu kluczy.

## Przed czym to nie chroni

Żadna aplikacja nie ochroni swoich danych przed kontem, na którym działa:

- **Oprogramowanie działające jako Ty** — złośliwy program albo ktoś korzystający
  z Twojej odblokowanej sesji — może odczytać zapisane logowanie z magazynu
  poświadczeń, PIN-y widoczne na ekranie lub na liście wdrożenia oraz
  wyeksportowane pliki.
- **PIN-ów w pamięci** działającego programu nie da się niezawodnie wymazać.
  Znikają po zamknięciu aplikacji; nie zostawiaj otwartej listy po zakończonym
  wdrożeniu.
- **Menedżer schowka, który ignoruje oznaczenie sekretu**, zachowa skopiowany PIN.
- **Szkic e-maila** przekazuje PIN programowi pocztowemu, który przechowuje szkice
  i wysłane wiadomości według własnych zasad.

Co ogranicza szkody: tymczasowy PIN jest bezużyteczny bez fizycznego klucza,
a przy opcji *Wymuś zmianę PIN-u przed pierwszym użyciem* przestaje działać przy
pierwszym logowaniu użytkownika. Pracuj na zaufanej stacji administratora, blokuj
ją, gdy odchodzisz, a na współdzielonym komputerze wyloguj się z KeyEnroll.

## Z czym łączy się KeyEnroll { #what-keyenroll-communicates-with }

| Cel | Kiedy | Co |
|---|---|---|
| Twój dostawca tożsamości | Logowanie, wyszukiwanie użytkowników, rejestracja, lista poświadczeń | Żądania potrzebne do tych działań, autoryzowane Twoim logowaniem. |
| Klucz bezpieczeństwa | Rejestracja | Polecenia FIDO przez USB lub NFC. |
| `api.github.com` | Tylko po kliknięciu **Sprawdź aktualizacje** | Pytanie o numer najnowszego wydania. Nie są wysyłane żadne dane o Tobie ani o tenancie. |

Nie ma telemetrii, statystyk użycia ani połączeń w tle.

## Log

Log zapisuje, co aplikacja zrobiła, oraz błędy — po to, żeby zgłoszenie problemu
było użyteczne. Jest ograniczony do czterech plików po 1 MB; starsze wpisy są
nadpisywane.

Zawiera nazwy użytkowników, dla których rejestrowano klucze, i adresy Twojego
tenanta, więc przeczytaj go, zanim dołączysz go do publicznego zgłoszenia.

## Gdy plik ustawień jest uszkodzony { #if-the-settings-file-is-damaged }

Jeśli `config.json` nie da się odczytać, KeyEnroll go nie nadpisuje. Plik jest
odkładany pod nazwą kończącą się na `.unreadable-<data>`, aplikacja startuje
z ustawieniami domyślnymi i o tym informuje. Zapisane logowania pozostają
nienaruszone.

## Usunięcie wszystkiego

1. Wyloguj się ze wszystkich instancji (to usuwa zapisane logowania) albo usuń
   instancje.
2. Odinstaluj aplikację.
3. Usuń folder ustawień.

## Zgłaszanie problemu z bezpieczeństwem

Nie opisuj podatności w publicznym zgłoszeniu. Najpierw skontaktuj się z opiekunem
projektu prywatnie, korzystając z danych kontaktowych na
[stronie projektu](https://github.com/inowakowski/KeyEnroll).
