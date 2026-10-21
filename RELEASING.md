# Wydawanie wersji i podpisywanie

Procedura dla opiekuna projektu. Opisuje zwykłe wydanie, wersję testową (preview),
własny podpis wydań, który sprawdza aplikacja przy aktualizacji, oraz darmowe
podpisywanie instalatorów Windows przez SignPath Foundation.

Decyzja z 2026-10-21: **tylko darmowe sposoby**. Płatnych certyfikatów (Certum,
Sectigo, Apple Developer Program) na razie nie kupujemy; ostatni rozdział mówi,
co by dały.

## Co chroni użytkownika przy aktualizacji

| Zabezpieczenie | Przed czym chroni | Koszt |
|---|---|---|
| Suma SHA-256 podawana przez GitHub dla każdego pliku | Uszkodzony albo podmieniony w drodze plik | 0 zł, działa od razu |
| **Własny podpis Ed25519** pliku `SHA256SUMS` | Podmieniony plik **także po przejęciu konta GitHub**: klucz prywatny nigdy tam nie trafia | 0 zł, jeden krok przy wydaniu |
| Podpis Authenticode od SignPath Foundation | Ostrzeżenie Windows „nieznany wydawca”, zmiana pliku po podpisaniu | 0 zł, trzeba złożyć wniosek |

Aplikacja instaluje aktualizację tylko wtedy, gdy plik zgadza się z sumą z GitHuba.
Gdy w `src/keyenroll/release_key.py` jest klucz publiczny, musi się też zgadzać
podpis. Wydanie bez podpisu jest wtedy odrzucane, a użytkownik dostaje odnośnik
do strony pobierania.

## Zwykłe wydanie

1. Gałąź od `main`, np. `release-0.8.0`. Zmień numer w `src/keyenroll/__init__.py`
   i `pyproject.toml` (oba muszą być takie same).
2. Pull request, zielone CI, scalenie. Bezpośredni push do `main` blokuje reguła
   repozytorium.
3. Opcjonalnie próbny build bez wydania: *Actions → build → Run workflow* na
   gałęzi wydania. Buduje instalatory sześciu platform jako artefakty.
4. Tag na commicie scalającym, np. z GitHub CLI:

    ```bash
    gh api -X POST repos/inowakowski/KeyEnroll/git/refs -f ref=refs/tags/v0.8.0 -f sha=<commit>
    ```

5. Workflow `build.yml` buduje instalatory i tworzy wydanie z ośmioma plikami.
   Z włączonym podpisywaniem wydanie zostaje **szkicem** (patrz niżej) i nikt go
   nie widzi, dopóki go nie podpiszesz.

## Wersja testowa (preview)

Numer i tag z myślnikiem: `0.8.0-preview.1`, `v0.8.0-preview.1`. Workflow oznacza
takie wydanie jako *Pre-release*:
- przycisk pobierania w dokumentacji i sprawdzanie aktualizacji w aplikacji go
  pomijają, chyba że użytkownik włączył *Uwzględniaj wersje testowe*,
- osoba z wersją testową dostanie później informację o wydaniu `0.8.0`,
- paczka `.deb` ma w środku numer `0.8.0~preview.1`, żeby Debian uznał `0.8.0`
  za nowszą. GitHub w nazwie pliku zamienia `~` na `.`.

## Własny podpis wydań

### Jednorazowo: klucz

1. Na swoim komputerze, z katalogu repozytorium:

    ```bash
    python tools/release_signing.py generate --key D:/keyenroll/release.key
    ```

    Skrypt pyta dwa razy o hasło (co najmniej 12 znaków), zapisuje zaszyfrowany
    klucz prywatny i wypisuje wiersz z kluczem publicznym.
2. **Przechowywanie:** plik klucza trzymaj poza repozytorium, najlepiej na
   pendrivie albo w menedżerze haseł, a hasło osobno. Zrób kopię zapasową w drugim
   miejscu. Bez klucza nie podpiszesz kolejnej wersji, a aplikacje z tym kluczem
   nie przyjmą aktualizacji (patrz „Utrata klucza”).
3. Wklej wypisany wiersz do `src/keyenroll/release_key.py`:

    ```python
    PUBLIC_KEYS: tuple[str, ...] = ("<klucz publiczny>",)
    ```

    i wprowadź to przez pull request. Od wersji, która zawiera klucz, aplikacja
    wymaga podpisu przy każdej aktualizacji.
4. W repozytorium: *Settings → Secrets and variables → Actions → Variables* dodaj
   zmienną `SIGN_RELEASES` o wartości `true`. Od teraz workflow tworzy wydania
   jako szkice.

Kolejność ma znaczenie: **pierwsze wydanie z kluczem w aplikacji musi już być
podpisane**. Inaczej aplikacje sprzed tej wersji przyjmą je normalnie, ale następne
aktualizacje nie będą możliwe bez podpisu.

### Przy każdym wydaniu

1. Wydanie powstaje jak wyżej i czeka jako szkic.
2. Podpisz je i opublikuj:

    ```bash
    python tools/release_signing.py sign v0.8.0 --key D:/keyenroll/release.key --publish
    ```

    Skrypt pobiera pliki szkicu przez GitHub CLI (`gh` musi być zalogowany),
    porównuje je z sumami, które podaje GitHub, i przerywa przy niezgodności.
    Następnie zapisuje `SHA256SUMS` i `SHA256SUMS.sig`, dołącza je do wydania
    i je publikuje.
3. Sprawdź wynik tak, jak zrobi to aplikacja:

    ```bash
    python tools/release_signing.py verify v0.8.0
    ```

### Wymiana klucza

1. Wygeneruj nowy klucz i dopisz jego klucz publiczny **obok** starego
   w `PUBLIC_KEYS`.
2. Wydaj wersję z oboma kluczami, **podpisaną starym**.
3. Od następnego wydania podpisuj nowym. Stary klucz usuń z `PUBLIC_KEYS` po kilku
   wersjach, gdy prawie nikt nie ma już wersji, która zna tylko stary.

### Utrata albo wyciek klucza

- **Klucz zgubiony:** aplikacje, które znają tylko ten klucz, nie przyjmą żadnej
  nowej aktualizacji z poziomu aplikacji. Wydaj wersję z nowym kluczem i poproś
  użytkowników o jednorazową ręczną instalację ze strony pobierania; potem
  aktualizacje znów działają.
- **Klucz wyciekł:** od razu wydaj wersję z nowym kluczem (bez starego) i opisz
  sytuację w notatce wydania. Do tego czasu ktoś z kluczem mógłby podpisać obce
  pliki, ale musiałby jeszcze opublikować je na GitHubie projektu.

## Darmowe podpisywanie instalatorów Windows: SignPath Foundation

SignPath Foundation podpisuje za darmo projekty open source. Wydawcą w podpisie
jest wtedy „SignPath Foundation”, a nie Ty.

**Warunki** ([signpath.org/terms](https://signpath.org/terms)): licencja OSI
(MIT spełnia) bez komercyjnej licencji podwójnej, brak zamkniętego kodu, projekt
utrzymywany i już wydany, opis funkcji na stronie pobierania, automatyczny build
z repozytorium w GitHub Actions oraz **zasady podpisywania opublikowane na stronie
projektu**.

**Kroki:**
1. Dodaj do dokumentacji stronę „Code signing policy”. Wzór poniżej.
2. Złóż wniosek na [signpath.org](https://signpath.org/), podając repozytorium
   i stronę z zasadami.
3. Po akceptacji SignPath przekaże dane projektu. Do `build.yml` dochodzi wtedy
   krok `signpath/github-action-submit-signing-request`, który wysyła nieodpisany
   instalator Windows i dostaje podpisany. Zrobimy to razem, gdy będzie
   akceptacja.
4. Własny podpis `SHA256SUMS` robisz dalej po swojemu: obejmuje on już podpisane
   instalatory.

**Wzór zasad podpisywania** (do strony dokumentacji, po angielsku):

> Free code signing provided by [SignPath.io](https://about.signpath.io/),
> certificate by [SignPath Foundation](https://signpath.org/).
> Committers and approvers: Ignacy Nowakowski. Every signed file is built by
> GitHub Actions from this public repository; nothing is signed by hand. Releases
> are approved by the maintainer before signing. KeyEnroll does not transfer any
> information to other networked systems unless the user asks for it: the
> identity provider the user signs in to, and api.github.com when the user checks
> for updates.

## Czego na razie nie robimy (płatne)

| Co | Koszt | Co by dało |
|---|---|---|
| Certyfikat OV dla Windows (np. Certum Standard, Sectigo) | ok. 109–440 € lub $ rocznie, klucz na tokenie, ważność najwyżej 460 dni | Podpis na Twoje nazwisko zamiast SignPath |
| Apple Developer Program | 99 $ rocznie | Podpis i notaryzacja dla macOS: brak ostrzeżenia Gatekeepera przy pierwszym uruchomieniu |
| Azure Artifact Signing | ok. 10 $ miesięcznie | Niedostępne dla osób prywatnych w UE, tylko dla firm |

Ostrzeżenie SmartScreen w Windows nie znika od razu nawet z podpisem: reputacja
buduje się z czasem i liczbą pobrań.
