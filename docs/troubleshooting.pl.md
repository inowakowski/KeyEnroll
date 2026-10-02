# Rozwiązywanie problemów

Znajdź komunikat, który widzisz, albo sytuację, w której jesteś.

## Klucz nie jest wykrywany

| System | Sprawdź |
|---|---|
| Windows | Aplikacja musi działać **jako administrator**. Jeśli widać żółty pasek, kliknij **Uruchom jako administrator**. |
| Linux | Jeśli klucz pojawia się tylko po uruchomieniu aplikacji jako root, brakuje reguł udev dla kluczy FIDO. Zainstaluj `libu2f-udev` lub `libfido2`, a potem wyjmij i włóż klucz. |
| Czytniki NFC | Musi działać usługa PC/SC (`pcscd` w Linuksie; usługa *Karta inteligentna* w Windows). |
| Wszystkie | Kliknij **Odśwież**. Wypróbuj inny port USB i unikaj hubów bez zasilania. Zamknij inne programy, które mogą zajmować klucz, np. przeglądarkę z otwartym oknem klucza bezpieczeństwa. |

Komunikat *Nie wykryto klucza bezpieczeństwa* w trakcie rejestracji oznacza to samo:
klucz nie był widoczny w chwili rozpoczęcia rejestracji.

## Logowanie

**Przeglądarka pokazuje błąd dotyczący redirect URI.**
Redirect URI w instancji i w rejestracji aplikacji różnią się. Muszą być identyczne,
łącznie z portem i ścieżką.

**„Cannot listen on port …”.**
Inny program na Twoim komputerze używa portu z redirect URI. Zamknij go albo
zarejestruj redirect URI z innym portem i wpisz go w instancji.

**Przeglądarka skończyła, a KeyEnroll nadal czeka.**
Przeglądarka nie mogła połączyć się z `http://localhost`. Blokują to niektóre
rozszerzenia bezpieczeństwa i firmowe proxy; zezwól na `localhost` albo ustaw inną
przeglądarkę jako domyślną.

**„Sesja wygasła.”**
Zaloguj się ponownie. O tym, jak długo ważne jest logowanie, decyduje dostawca
tożsamości.

**W Linuksie trzeba logować się po każdym uruchomieniu.**
Nie ma usługi Secret Service, w której można zapisać logowanie. Użyj środowiska
z GNOME Keyring lub KWallet.

## Wyszukiwanie użytkowników

**Nie znaleziono żadnego użytkownika.**
U większości dostawców wyszukiwanie dopasowuje *początek* imienia, nazwiska, nazwy
użytkownika lub adresu e-mail. Wpisz pierwsze litery, nie fragment ze środka.
Sprawdź też, czy wybrana jest właściwa instancja; lista pokazuje najwyżej 25 wyników.

**Błąd dostawcy wspominający o uprawnieniach lub „forbidden”.**
Rejestracji aplikacji brakuje uprawnienia albo zgody administratora, albo Twoje
konto nie ma wymaganej roli. Zobacz [Dostawcy tożsamości](providers.md).

## W trakcie rejestracji

| Komunikat | Co oznacza i co zrobić |
|---|---|
| *Reset nie został przyjęty. Trzeba go potwierdzić w ciągu kilku sekund od włożenia klucza.* | Klucz pozwala na reset tylko chwilę po włożeniu. Wyjmij go, włóż i dotknij, gdy tylko zacznie migać. Aplikacja ponawia próbę kilka razy. |
| *Klucz nie został dotknięty na czas.* | Dotknij złotego styku lub przycisku klucza, gdy miga. |
| *Upłynął czas oczekiwania na klucz.* | Klucza nie wyjęto lub nie włożono ponownie w ciągu dwóch minut. Zacznij od nowa. |
| *Wybrany klucz nie jest już podłączony.* | Klucz został wyjęty. Włóż go i kliknij **Odśwież**. |
| *Błędny PIN.* z liczbą pozostałych prób | Obecny PIN klucza wpisano z błędem. Uważaj na licznik: gdy dojdzie do zera, PIN zostanie zablokowany. |
| *Zbyt wiele błędnych prób PIN-u. Włóż klucz ponownie i spróbuj jeszcze raz.* | Po trzech błędnych PIN-ach z rzędu klucz wstrzymuje próby. Wyjmij go i włóż ponownie. |
| *PIN jest zablokowany. Klucz trzeba przywrócić do ustawień fabrycznych.* | Włącz opcję *Przywróć klucz do ustawień fabrycznych*. Wszystkie poświadczenia FIDO na kluczu przepadną. |
| *Klucz odrzucił ten PIN (za krótki lub zbyt prosty).* | Klucz wymusza politykę PIN-u. Wybierz PIN dłuższy lub mniej regularny. |
| *Obecny PIN jest krótszy niż minimalna długość PIN-u w profilu.* | Włącz *Ustaw nowy losowy PIN* lub reset fabryczny, żeby ustawić nowy PIN o wystarczającej długości. |
| *Ten klucz nie obsługuje…* | Klucz jest za stary na którąś opcję profilu albo nie został z nią wyprodukowany. Użyj innego profilu lub innego klucza. Zobacz [co musi obsługiwać klucz](profiles.md#what-the-key-has-to-support). |
| *Ten klucz jest już zarejestrowany dla tego użytkownika.* | Użytkownik ma już poświadczenie na tym kluczu. Usuń je najpierw na stronie [Poświadczenia](credentials.md) albo włącz reset fabryczny. |
| *Dostawca tożsamości zwrócił RP ID niezgodne z jego adresem (origin).* | Domena w instancji nie jest tą, dla której dostawca rejestruje klucze. Dla Okta wpisz domenę, na której logują się użytkownicy; dla PingOne AIC sprawdź pole *Origin WebAuthn*. |
| *Poświadczenie zostało zarejestrowane, ale nie udało się wymusić zmiany PIN-u.* | Klucz jest zarejestrowany i działa z tymczasowym PIN-em, ale użytkownik nie zostanie zmuszony do jego zmiany. Poproś użytkownika, żeby zmienił PIN samodzielnie. |
| Tekst błędu od dostawcy tożsamości | Wyświetlany w otrzymanej postaci. Typowe przyczyny: metoda FIDO2 nie jest włączona dla użytkownika, polityka tenanta nie akceptuje tego modelu klucza albo brakuje uprawnienia. |

## Wdrożenie masowe

**Wielu użytkowników ma status „Nie znaleziono”.**
Identyfikatory w pliku nie są w postaci oczekiwanej przez dostawcę (np. krótki login
zamiast pełnej nazwy użytkownika) albo wybrana jest zła instancja.

**„Klucz … został już zarejestrowany w tym wdrożeniu.”**
Ten sam klucz włożono dla drugiego użytkownika. Weź następny klucz.

**„Ta lista należy do innej instancji.”**
Wróć do instancji, dla której wczytano listę, albo wyeksportuj wyniki i wyczyść
listę.

**Wyeksportowany plik otwiera się z całą zawartością w jednej kolumnie.**
Arkusz oczekuje innego separatora. Wyeksportuj ponownie i wybierz drugi format
(średnik lub przecinek).

## Sama aplikacja

**Ostrzeżenie, że nie udało się odczytać pliku ustawień.**
Zobacz [Dane i bezpieczeństwo](data.md#if-the-settings-file-is-damaged).

**„Wystąpił nieoczekiwany błąd”.**
Szczegóły są w logu. Prosimy o zgłoszenie.

## Zgłaszanie problemu { #reporting-a-problem }

1. Zanotuj wersję (*Ustawienia → O programie*) i system operacyjny.
2. Jeśli możesz, odtwórz problem ze szczegółowym logowaniem: uruchom aplikację
   z opcją `--log-level DEBUG`, patrz [opcje uruchamiania](install.md#start-up-options).
3. Otwórz *Ustawienia → Otwórz folder z ustawieniami i logami* i weź plik
   `logs/keyenroll.log`. **Najpierw go przeczytaj**: zawiera nazwy użytkowników
   i adresy tenanta, choć nie ma w nim PIN-ów ani tokenów.
4. Opisz, co zostało zrobione i co się stało, w
   [zgłoszeniach projektu](https://github.com/inowakowski/KeyEnroll/issues).
