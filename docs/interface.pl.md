# Okno aplikacji w skrócie

Ta strona wyjaśnia, do czego służy każda część okna. Każda strona aplikacji ma
własny rozdział ze szczegółami.

![Okno główne](assets/screenshots/pl/enroll.png){ .shot }

## Trzy obszary

**Pasek boczny (po lewej).** Przełącza między sześcioma stronami aplikacji. Na dole
widać numer używanej wersji.

**Górny pasek.** Jest wspólny dla wszystkich stron:

| Element | Do czego służy |
|---|---|
| Tytuł strony | Strona, na której jesteś. |
| Lista instancji | Tenant, z którym pracujesz. Wszystko, co wyszukujesz, rejestrujesz lub usuwasz, dotyczy instancji wybranej tutaj. Zobacz [Instancje i logowanie](instances.md). |
| Znacznik sesji | **Zalogowano** (zielony) albo **Nie zalogowano** — dla wybranej instancji. |
| **Zaloguj** / **Wyloguj** | Otwiera w przeglądarce stronę logowania dostawcy tożsamości albo kończy sesję i usuwa zapisane logowanie. |

**Strona (środek).** Obszar roboczy wybranej strony.

W systemie Windows nad stroną pojawia się żółty pasek, jeśli aplikację uruchomiono
bez uprawnień administratora; zobacz [Instalacja](install.md#windows).

## Strony

| Strona | Do czego służy | Szczegóły |
|---|---|---|
| **Rejestracja** | Przygotowanie jednego klucza i zarejestrowanie go dla jednego użytkownika. | [Rejestracja klucza](enroll.md) |
| **Wdrożenie masowe** | Rejestracja kluczy dla całej listy użytkowników wczytanej z pliku i eksport tymczasowych PIN-ów. | [Wdrożenie masowe](bulk.md) |
| **Poświadczenia** | Sprawdzenie, jakie klucze ma zarejestrowane użytkownik, i usunięcie wybranego. | [Poświadczenia](credentials.md) |
| **Profile** | Zestawy opcji rejestracji do wielokrotnego użycia. | [Profile](profiles.md) |
| **Instancje** | Dodawanie, edycja i usuwanie tenantów dostawców tożsamości. | [Instancje i logowanie](instances.md) |
| **Ustawienia** | Kolorystyka, język, wiadomość dla użytkownika, aktualizacje, logi. | [Ustawienia](settings.md) |

## Co działa wszędzie

**Sortowanie tabel.** Kliknij nagłówek kolumny, żeby posortować listę użytkowników,
poświadczeń lub instancji; drugie kliknięcie odwraca kolejność, trzecie przywraca
pierwotną. Wielkość liter nie ma znaczenia, a liczby w nazwach są porównywane jak
liczby (`user2` jest przed `user10`).

**Szerokość kolumn.** Przeciągnij granicę między nagłówkami kolumn. Szerokie listy
przewijają się w poziomie, zamiast ucinać tekst.

**Podział strony Rejestracja.** Przeciągnij granicę między listą użytkowników
a opcjami, żeby dać więcej miejsca jednej ze stron.

**Układ okna.** Rozmiar i położenie okna oraz podział strony są zapamiętywane.

**Kopiowanie PIN-u.** Zawsze gdy kopiujesz PIN lub wiadomość, która go zawiera,
schowek jest czyszczony po minucie.

**W trakcie rejestracji.** Lista instancji i przycisk logowania są zablokowane,
a zamknięcie okna wymaga potwierdzenia.
