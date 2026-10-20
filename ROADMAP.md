# Plan rozwoju KeyEnroll

Stan na 2026-10-20. Funkcje 1–5 i 7 zatwierdził właściciel projektu, a tryb wiersza
poleceń (6) został odłożony. Każde wydanie kończy się aktualizacją dokumentacji EN i PL,
nowymi zrzutami ekranu (`tools/docs_screenshots.py`) i listą rzeczy, które trzeba
sprawdzić na prawdziwym kluczu albo tenancie.

| Wydanie | Zakres | Kto sprawdza |
|---|---|---|
| **0.5.1** | poprawki z dwóch przeglądów, dokumentacja na GitHub Pages | symulator i jedna rejestracja na kluczu |
| **0.6.0** | (3) eksport i import konfiguracji, (4) dziennik wdrożeń, (5) dozwolone modele kluczy | symulator, a na kluczu tylko (5) |
| **0.7.0** | (1) istniejące klucze użytkownika, (2) lista z grupy w katalogu | **żywe tenanty** każdego dostawcy |
| **0.8.0** | (7) etykiety i karty przekazania (PDF i druk) | drukarka, czytnik PDF |
| później | polecenia tylko do odczytu w wierszu poleceń | – |

Funkcje, które da się w pełni sprawdzić na symulatorze, wchodzą przed tymi, które
zmieniają komunikację z dostawcami.

---

## Faza 0 – wydanie 0.5.1

### Poprawki
1. Scalić PR #4: odrzucanie innego klucza przy resecie, zachowanie logowania przy
   braku sieci, `clientExtensionResults` dla Entra, sprawdzanie redirect URI.
2. Druga sesja (gałąź `review-performance-docs`, jeszcze niewypchnięta) robi rebase
   na `main` po PR #4 i otwiera własny PR. Wnosi przyspieszenie tabeli wdrożenia
   masowego, równoległe wyszukiwanie użytkowników, ponawianie zapisu konfiguracji,
   CHANGELOG, CONTRIBUTING i SECURITY. Konflikty spodziewane są w `README.md`,
   `docs/bulk*.md` i `docs/troubleshooting*.md`. Jej własny `ROADMAP.md` należy
   zastąpić tym plikiem.
3. Podnieść wersję do 0.5.1 (`src/keyenroll/__init__.py`, `pyproject.toml`), wpisać
   ją do CHANGELOG i wypchnąć tag `v0.5.1`.

### Dokumentacja na GitHub Pages
Źródła zostają w folderze `docs/` na `main`, bez gałęzi `gh-pages`. Dokumentacja
zmienia się w tym samym PR co funkcja, którą opisuje, a testy pilnują obu języków.

- `.github/workflows/docs.yml`:
  - zadanie `build` bez zmian: `mkdocs build --strict` przy każdym PR i pushu,
  - nowe zadanie `deploy`, uruchamiane przy tagu `v*` i ręcznie
    (`workflow_dispatch`). Kroki: `actions/configure-pages` (jego wynik `base_url`
    trafia do zmiennej `SITE_URL`), `mkdocs build --strict`,
    `actions/upload-pages-artifact`, `actions/deploy-pages`,
  - uprawnienia `pages: write` i `id-token: write` tylko dla zadania `deploy`.
- Adres strony nadal nie trafia do repozytorium. Test
  `test_no_host_of_the_site_is_built_in` zostaje, a odnośnik *Dokumentacja*
  w aplikacji dalej prowadzi do README.
- README (sekcja „Budowanie dokumentacji”) i komentarz w workflow: GitHub Pages
  zamiast Cloudflare.

**Do zrobienia przez właściciela:**
- *Settings → Pages → Source: GitHub Actions*.
- *Settings → Environments → github-pages → Deployment branches and tags*: dodać
  regułę tagu `v*`. Bez niej wdrożenie z tagu zostanie zablokowane.
- Wpisać adres strony w pole *Website* w opisie repozytorium.
- Jeśli projekt w Cloudflare Pages istnieje, wyłączyć go.

---

## Wydanie 0.6.0

### (3) Eksport i import konfiguracji
Przeniesienie instancji, profili i szablonu wiadomości na inne stanowisko
administratora. Plik nie zawiera sekretów, bo tokeny zostają w magazynie systemu.

- **Format:** JSON
  `{"format": "keyenroll-config", "version": 1, "app": "0.6.0", "instances": [...],
  "profiles": [...], "message": {...}}`. Nie zawiera `ui`, `active_instance`, motywu
  ani języka.
- **Kod:** `config.py` (`export_data()`, `import_data()`, walidacja), nowe okno
  `ImportDialog` (co zaimportować, co zrobić z powtórzoną nazwą: pominąć, zastąpić
  albo dodać jako „nazwa (2)”), przyciski na stronie *Instancje* albo w
  *Ustawieniach*.
- **Zasady:**
  - zaimportowane instancje dostają **nowe ID**, bo tokeny w magazynie są
    zapisane pod ID,
  - nieznany typ dostawcy i brak wymaganych pól odrzucają cały wpis z czytelnym
    komunikatem,
  - plik nie może przekraczać 1 MB,
  - odwołania `default_profile` do profili, które nie zostały zaimportowane, są
    czyszczone,
  - po imporcie trzeba się zalogować w każdej nowej instancji.
- **Testy:** eksport i import tam i z powrotem, powtórzone nazwy, nowe ID, odrzucanie
  błędnych plików, brak tokenów w pliku.
- **Dokumentacja:** `instances.md` i `instances.pl.md` (nowa sekcja „Przenoszenie
  konfiguracji”), `data.md` (zawartość pliku).

### (4) Dziennik wdrożeń
Zapis każdej rejestracji, pojedynczej i masowej, do audytu. **Bez PIN-ów.**

- **Plik:** `config_dir()/journal/deployments-RRRR-MM.csv`, jeden plik na miesiąc,
  dopisywany z prawami tylko dla właściciela (`write_private` trzeba rozszerzyć
  o dopisywanie).
- **Pola:**
  - czas (UTC, ISO 8601), wynik (zarejestrowano lub błąd z komunikatem),
  - instancja, dostawca, administrator,
  - użytkownik (login, ID, nazwa),
  - numer seryjny, firmware, AAGUID i nazwa klucza,
  - profil, „PIN zmieniony”, „wymuszona zmiana PIN-u”.
- **Administrator:** pole `id_token` w `TokenSet`, odczyt claimów `preferred_username`,
  `email` i `sub` (bez weryfikacji podpisu, bo token przychodzi bezpośrednio z
  endpointu przez TLS i służy tylko do opisu). Jeśli odświeżenie nie zwróci
  `id_token`, zostaje wartość z logowania, a w ostateczności „nieznany”. Okta
  i PingOne dostają dziś tylko `openid`; dodanie zakresu `profile` trzeba sprawdzić
  na żywym tenancie, więc w 0.6.0 tylko jako fallback do `sub`.
- **Ustawienia:** włączony domyślnie, czas przechowywania (domyślnie 12 miesięcy;
  starsze pliki usuwane przy starcie), przycisk *Otwórz dziennik*.
- **Kod:**
  - nowy moduł `journal.py`,
  - wywołania w `EnrollPage._on_done` i `_on_failed` oraz w `BulkRunner`
    po każdym wierszu,
  - nowe pola `aaguid` i `firmware` w `EnrollResult` i `KeyInfo`.
- **Testy:**
  - pola i kodowanie CSV, ochrona przed formułami jak w eksporcie,
  - brak PIN-u w żadnym polu,
  - rotacja i czyszczenie starych plików, prawa do pliku.
- **Dokumentacja:**
  - `data.md`: co jest w dzienniku, że to dane osobowe (RODO), przechowywanie,
  - `settings.md`: nowe opcje,
  - `bulk.md` i `enroll.md`: jedna linijka każdy.

### (5) Dozwolone modele kluczy
Profil może ograniczyć, jakie klucze wolno rejestrować. Sprawdzenie odbywa się
**przed resetem fabrycznym**, bo dziś zły klucz jest najpierw wymazywany, a dopiero
potem odrzucany przez politykę dostawcy.

- **Profil:** nowe pola `allowed_aaguids: list[str]` (puste oznacza każdy model)
  i `min_firmware: str` (puste oznacza brak wymagań). Starsze wersje aplikacji
  ignorują nieznane pola, więc format pliku konfiguracji się nie zmienia.
- **Silnik:** `Enroller._precheck` porównuje `ctap.info.aaguid` z listą, a firmware
  z `describe()`. Firmware da się odczytać tylko przez USB i tylko z YubiKey; gdy jest
  wymagany, a nieznany, klucz jest odrzucany.
- **UI:**
  - w formularzu profilu lista dozwolonych modeli z przyciskiem *Dodaj podłączony
    klucz*, który odczytuje AAGUID i nazwę produktu, oraz ręcznym wpisywaniem,
  - pole minimalnej wersji firmware,
  - podsumowanie profilu pokazuje ograniczenie, a strona *Rejestracja* ostrzega
    zawczasu, gdy wybrany klucz nie pasuje.
- **Testy:** symulator z innym AAGUID jest odrzucany bez resetu, a pasujący przechodzi;
  nieznany firmware przy wymaganej wersji jest odrzucany.
- **Dokumentacja:** `profiles.md` (nowa opcja i przykład „tylko YubiKey 5 z firmware
  5.7+”), `troubleshooting.md` (nowe komunikaty).
- **Na kluczu:** AAGUID i firmware prawdziwego YubiKey, odrzucenie innego modelu
  przed resetem.

---

## Wydanie 0.7.0 – wymaga testów na żywych tenantach

### Wspólne: stronicowanie u dostawców
Dziś każde wyszukiwanie zwraca maksymalnie 25 wyników. Grupy i listy poświadczeń
potrzebują stronicowania, więc najpierw w `providers/base.py` powstaje wspólny
helper:
- Entra: `@odata.nextLink`,
- Okta: nagłówek `Link: rel="next"`,
- PingOne: `_links.next`,
- AIC: `_pagedResultsCookie`.

Obowiązuje limit bezpieczeństwa liczby stron, a limity zapytań (429) obsługuje
istniejący mechanizm ponowień.

### (1) Istniejące klucze użytkownika
- **Wdrożenie masowe:**
  - nowa kolumna „Metody FIDO”, liczona podczas wyszukiwania użytkowników
    (`list_credentials`),
  - opcja *Pomiń użytkowników, którzy mają już klucz*, która zmienia status takich
    wierszy na nowy „Ma już klucz”. Wiersz można przywrócić do kolejki, tak jak
    nieudany.
- **Rejestracja pojedyncza:** po wybraniu użytkownika pod listą pojawia się wiersz
  „ma już N metod FIDO”.
- **Ograniczenia:**
  - PingOne AIC nie ma listy poświadczeń, więc kolumna pokazuje „—”,
  - Entra (np. passkeys w Microsoft Authenticator) i Okta (Windows Hello) zwracają
    też passkeys, dlatego etykieta mówi o „metodach FIDO”, nie o kluczach,
  - jedno dodatkowe zapytanie na użytkownika sumuje się z limitami przy
    równoległym wyszukiwaniu,
  - sprawdzanie można wyłączyć.
- **Testy:** symulowane odpowiedzi każdego dostawcy, pomijanie, przywracanie.
- **Dokumentacja:** `bulk.md` (statusy i opcja), `enroll.md`.

### (2) Lista z grupy w katalogu
- **Opcja dla każdej instancji**: *Import z grup* wymaga dodatkowego uprawnienia
  w rejestracji aplikacji:
  - Entra: `GroupMember.Read.All`,
  - Okta: `okta.groups.read`,
  - PingOne: rola administratora z odczytem grup,
  - AIC: `fr:idm:*` już jest.
  
  Zakres jest dodawany do logowania tylko po włączeniu opcji. Bez niej aplikacja
  działa z obecną rejestracją z dokumentacji YubiEnroll.
- **Interfejs:** przycisk *Wczytaj z grupy…* obok *Wczytaj z pliku…* otwiera okno
  wyszukiwania grupy, pokazuje liczbę członków i dla Entra pyta o członków
  pośrednich (podgrupy).
- **API (do sprawdzenia na żywo):**

  | Dostawca | Wyszukanie grupy | Członkowie |
  |---|---|---|
  | Entra | `GET /groups?$filter=startswith(displayName,'…')` | `/groups/{id}/members/microsoft.graph.user` lub `/transitiveMembers/microsoft.graph.user` |
  | Okta | `GET /api/v1/groups?q=…` | `GET /api/v1/groups/{id}/users` |
  | PingOne | `GET /groups?filter=name sw "…"` | `GET /users?filter=memberOfGroups[id eq "…"]` |
  | AIC (opcjonalnie) | `managed/alpha_group?_queryFilter=…` | `managed/alpha_group/{id}/members` |

- **Kod:**
  - w dostawcach `search_groups()` i `group_members()` oraz flaga
    `supports_groups`,
  - użytkownicy z grupy są od razu w stanie *Gotowy*, bez dodatkowego wyszukiwania,
  - lista pamięta, z której instancji i grupy pochodzi.
- **Testy:** stronicowanie, filtrowanie samych użytkowników, zakres dodawany tylko
  przy włączonej opcji.
- **Dokumentacja:**
  - `providers.md`: dodatkowe uprawnienie dla każdego dostawcy, zgoda
    administratora,
  - `bulk.md`: druga metoda wczytania listy,
  - `instances.md`: nowa opcja instancji.
- **Na żywo:** każdy dostawca, grupa ponad 200 osób (stronicowanie), grupa
  zagnieżdżona w Entra.

---

## Wydanie 0.8.0

### (7) Etykiety i karty przekazania
- **Etykieta klucza:**
  - zawartość: nazwa wyświetlana, login, nazwa i numer seryjny klucza, data,
  - rozmiary do wyboru: 62×29 mm (taśma Brother DK) i arkusz A4 3×8 (70×37 mm),
  - **nigdy nie zawiera PIN-u**.
- **Karta przekazania:**
  - zawiera treść wiadomości dla użytkownika,
  - PIN jest drukowany **tylko na osobnej kartce i tylko po zaznaczeniu opcji**,
    domyślnie wyłączonej, żeby karta i klucz mogły trafić do użytkownika różnymi
    drogami.
- **Gdzie:** okno wyniku rejestracji (*Drukuj etykietę*, *Karta przekazania…*)
  oraz wdrożenie masowe (etykiety dla wszystkich zarejestrowanych, jedna strona
  arkusza A4).
- **Technika:** `QPdfWriter` i `QPrinter` z PySide6-Essentials, bez nowych
  zależności (sprawdzone na 6.11.2). PDF powstaje w pamięci (`QBuffer`) i jest
  zapisywany przez `write_private`, tak jak inne pliki z PIN-em. Bez kodów QR, bo
  wymagałyby nowej biblioteki.
- **Testy:**
  - PDF powstaje i ma oczekiwaną liczbę stron,
  - PIN nie występuje w tekście etykiety, a występuje tylko na stronie PIN-u, gdy
    jest zaznaczona opcja,
  - prawa do pliku.
- **Dokumentacja:** `enroll.md` (sekcja „Przekazanie klucza”), `bulk.md`, `data.md`
  (PDF z PIN-em to dane wrażliwe).

---

## Później: polecenia tylko do odczytu
Rejestracji kluczy z wiersza poleceń nie robimy. Na Windows jest YubiEnroll CLI,
a rejestracja i tak jest interaktywna (dotknięcie klucza, logowanie w przeglądarce).
Do tego PIN wypisany w terminalu trafia do historii.

Po 0.7.0 można rozważyć polecenia tylko do odczytu, na wszystkich systemach. Silnik
nie zależy od Qt, więc kosztują niewiele. Wymagają wcześniejszego zalogowania
w aplikacji.
- `keyenroll list-credentials --instance … --user …` w formacie JSON,
- raport „kto z grupy nie ma klucza”,
- eksport dziennika za wybrany okres,
- import konfiguracji.

---

## Zasady wspólne dla każdej funkcji
- Każdy nowy tekst w interfejsie ma tłumaczenie w pięciu językach (pilnuje tego
  `tests/test_i18n.py`). Wersje de, es, fr i it nadal nie są sprawdzone przez
  rodzimych użytkowników.
- Każda strona dokumentacji ma wersje `nazwa.md` i `nazwa.pl.md`, a
  `mkdocs build --strict` przechodzi.
- Zrzuty ekranu są generowane ponownie po każdej zmianie interfejsu.
- `ruff check src tests packaging tools` musi być czysty. Gdy zmiana dotyczy wątków
  lub zamykania okien, cały zestaw testów uruchamiamy trzy razy z rzędu.
- PIN nigdy nie trafia do logu, dziennika, konfiguracji ani etykiety.
- Każdy PR zawiera listę rzeczy do sprawdzenia na prawdziwym kluczu albo tenancie.

## Decyzje do podjęcia
1. GitHub Pages zamiast Cloudflare Pages i publikacja przy wydaniu (proponowane), czy
   publikacja po każdym pushu do `main`?
2. Dziennik wdrożeń domyślnie włączony z przechowywaniem 12 miesięcy?
3. Import z grup także dla PingOne AIC, czy tylko Entra, Okta i PingOne?
4. Rozmiary etykiet: wystarczą taśma 62 mm i arkusz A4 3×8?
5. Wymagana minimalna wersja firmware i nieznany firmware (NFC): odrzucać klucz
   (proponowane), czy tylko ostrzegać?
