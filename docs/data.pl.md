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
Service (GNOME Keyring, KWallet) w Linuksie.

## PIN-y

- Losowy PIN powstaje na Twoim komputerze, z użyciem systemowego generatora liczb
  losowych przeznaczonego do tajemnic.
- Do klucza jest przesyłany szyfrowanym kanałem określonym przez standard FIDO.
  **Nigdy nie trafia do dostawcy tożsamości** ani nigdzie indziej.
- Jest widoczny w oknie wyniku, a na liście wdrożenia masowego pozostaje do
  wyczyszczenia listy lub zamknięcia aplikacji. Nigdy nie jest zapisywany
  w ustawieniach ani w logu.
- Skopiowany PIN lub wiadomość znika ze schowka po minucie, chyba że w międzyczasie
  skopiowano coś innego.
- Pliki, które eksportujesz lub zapisujesz, zawierają PIN jawnym tekstem. W macOS
  i Linuksie są tworzone z dostępem tylko dla Twojego konta. Usuń je po wydaniu
  kluczy.

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
