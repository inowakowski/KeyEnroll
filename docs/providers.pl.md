# Dostawcy tożsamości

Przed pierwszym logowaniem u dostawcy tożsamości trzeba **zarejestrować aplikację**.
Dzięki niej dostawca wie, że KeyEnroll może logować administratorów i w ich imieniu
zarządzać kluczami bezpieczeństwa użytkowników.

KeyEnroll korzysta z **tej samej rejestracji co narzędzie YubiEnroll firmy Yubico**.
Yubico publikuje dla każdego dostawcy instrukcję krok po kroku ze zrzutami ekranu
(po angielsku); wykonaj ją, a otrzymane wartości wpisz w [instancji](instances.md)
KeyEnroll:

[YubiEnroll: konfiguracja dostawców tożsamości](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html){ .md-button }

Ta strona wymienia dla każdego dostawcy pola, o które pyta KeyEnroll, **na co muszą
pozwalać konta i sam tenant**, oraz miejsca, w których najczęściej coś idzie nie tak.

!!! info "Wspólne dla wszystkich dostawców"
    - Aplikację rejestruje się jako **klienta publicznego (natywnego)** z przepływem
      *authorization code* i PKCE. KeyEnroll nie przechowuje żadnego sekretu klienta.
    - **Redirect URI** musi zaczynać się od `http://localhost` i dokładnie zgadzać
      się z rejestracją. Podczas logowania KeyEnroll nasłuchuje pod tym adresem
      wyłącznie na Twoim komputerze.
    - Domyślne redirect URI nadal zawierają słowo `yubienroll`, żeby rejestracja
      wykonana dla YubiEnroll działała bez zmian. Jeśli zarejestrujesz inny adres,
      wpisz taki sam w instancji.

## Konta, których to dotyczy

Udział biorą trzy rodzaje kont, a każdy dostawca stawia im własne wymagania:

1. **Administrator konfigurujący** rejestruje aplikację i nadaje jej uprawnienia,
   raz na tenant. Później to konto nie jest używane w KeyEnroll.
2. **Operator** to administrator, który loguje się do KeyEnroll i rejestruje klucze.
   Wszystko, co robi KeyEnroll, dzieje się z uprawnieniami tego konta: uprawnienia
   aplikacji jedynie otwierają drzwi, a o tym, co wolno za nimi, decyduje rola
   operatora.
3. **Użytkownik** otrzymuje klucz. Jego konto musi istnieć u dostawcy i mieć prawo
   korzystać z kluczy bezpieczeństwa.

### Role administratorów w skrócie { #administrator-roles-at-a-glance }

| Dostawca tożsamości | Administrator konfigurujący | Operator (loguje się do KeyEnroll) |
|---|---|---|
| Microsoft Entra ID | *Application Administrator* lub *Cloud Application Administrator* do rejestracji; zgodę administratora może też nadać *Privileged Role Administrator* lub *Global Administrator* | *Authentication Administrator*; *Privileged Authentication Administrator* dla kluczy innych administratorów |
| Okta | *Super Administrator* lub *Application Administrator* | *Super Administrator*, *Organization Administrator* lub *Group Administrator* |
| PingOne PingID | Administrator, który może tworzyć aplikacje w środowisku | *Identity Data Admin* i *Environment Admin* |
| PingOne Advanced Identity Cloud | Administrator tenanta (aplikacja, journey, skrypt i sekrety) | Rola wewnętrzna `openidm-admin` oraz to, co sprawdza krok autoryzacji w journey (np. członkostwo w `webauthn-admins`) |

Szczegóły, a także to, na co musi pozwalać sam tenant, opisano niżej dla każdego
dostawcy.

## Microsoft Entra ID

| Pole | Co wpisać |
|---|---|
| **Identyfikator katalogu (tenant ID)** | Ze strony *Przegląd* rejestracji aplikacji. |
| **Identyfikator aplikacji (client ID)** | Z tej samej strony. |
| **Redirect URI** | Domyślnie `http://localhost/yubienroll-redirect`. |
| **Punkt końcowy Entra ID** | Zostaw `https://login.microsoftonline.com`. Zmień tylko dla chmur krajowych. |
| **Punkt końcowy Microsoft Graph** | Zostaw `https://graph.microsoft.com`. Zmień tylko dla chmur krajowych. |

### Rejestracja aplikacji

- *Rejestracje aplikacji → Nowa rejestracja*, platforma **Aplikacje mobilne
  i klasyczne** (klient publiczny/natywny). Redirect URI nie wymaga portu: Entra ID
  akceptuje dowolny port na `localhost`.
- **Uprawnienia interfejsu API**, Microsoft Graph, typ **Delegowane**:
    - `User.ReadBasic.All` — do wyszukiwania użytkowników;
    - `UserAuthenticationMethod.ReadWrite.All` — do rejestrowania, listowania
      i usuwania kluczy.

    KeyEnroll prosi też o standardowe `openid`, `profile` i `offline_access`, których
    nie trzeba dodawać osobno. **Nie** dodawaj uprawnień typu *Aplikacja*: przy
    uprawnieniach delegowanych aplikacja nigdy nie zrobi więcej niż zalogowany
    operator.
- **Udziel zgody administratora** dla tenanta. Microsoft pozwala na to rolom
  *Privileged Role Administrator*, *Cloud Application Administrator* i *Application
  Administrator*; instrukcja Yubico wymienia *Global Administrator*.
- Opcjonalnie: w *Aplikacjach dla przedsiębiorstw* ustaw **Wymagane przypisanie** na
  *Tak* i przypisz tylko operatorów, żeby nikt inny nie mógł zalogować się do
  KeyEnroll.

### Operator

- **Authentication Administrator**: rejestruje klucze użytkowników bez ról
  administracyjnych i nimi zarządza.
- **Privileged Authentication Administrator**: potrzebny dla użytkowników, którzy sami
  mają rolę administracyjną, w tym Global Administratorów.
- Operator **nie zarejestruje klucza na własnym koncie**: interfejs Microsoft do
  rejestracji kluczy w czyimś imieniu nie obsługuje samoobsługi. Skorzystaj z innego
  operatora albo ze strony *Informacje zabezpieczające* użytkownika.
- Logowanie operatora przechodzi przez zwykłe w tenancie uwierzytelnianie
  wieloskładnikowe i dostęp warunkowy.

### Ustawienia tenanta

W *Entra ID → Metody uwierzytelniania → Zasady → Passkey (FIDO2)*:

- Metoda jest **włączona** i **skierowana** do użytkowników, którzy dostają klucze
  (*Wszyscy użytkownicy* albo ich grupy). Członek grupy *wykluczonej* nie dostanie
  klucza, nawet jeśli obejmuje go inna grupa.
- **Allow self-service set up** ma wartość **Yes**. Bez tego interfejs Microsoft
  odmawia działania (znany problem Microsoft Graph), choć konfigurację wykonuje
  administrator, a nie użytkownik.
- Profil passkey obowiązujący użytkownika dopuszcza passkeye **powiązane
  z urządzeniem** (device-bound). Jeśli profil **wymusza atestację** albo
  **ograniczenia kluczy** (listę dozwolonych lub blokowanych AAGUID), wydawane modele
  kluczy muszą je spełniać.

### Użytkownicy

- Konta członków tenanta. **Goście (B2B)** nie mogą rejestrować passkeyów.
- Objęci polityką Passkey (FIDO2), jak wyżej.
- Bez dodatkowej licencji: passkeye są dostępne w każdej edycji Entra ID, także
  w bezpłatnej.

### Warto wiedzieć

- Nazwa klucza jest ograniczona do 30 znaków.
- Microsoft udostępnia interfejs rejestracji kluczy FIDO2, z którego korzysta
  KeyEnroll, tylko w chmurze globalnej; chmury US Government i Chiny (21Vianet) go
  nie obsługują (stan dokumentacji Microsoft Graph z lipca 2026). Oba pola z adresami
  punktów końcowych czekają na zmianę tej sytuacji.
- Źródła: [Yubico: Entra ID](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-entra.html),
  [Microsoft Graph: creationOptions](https://learn.microsoft.com/pl-pl/graph/api/fido2authenticationmethod-creationoptions?view=graph-rest-1.0),
  [Microsoft: włączanie passkeyów (FIDO2)](https://learn.microsoft.com/pl-pl/entra/identity/authentication/how-to-enable-passkey-fido2).

## Okta

| Pole | Co wpisać |
|---|---|
| **Domena Okta** | Na przykład `example.okta.com` albo własna domena. |
| **Client ID** | Aplikacji utworzonej na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:8080/yubienroll-redirect`. |

### Integracja aplikacji

- *Applications → Create App Integration*, metoda logowania **OIDC - OpenID
  Connect**, typ aplikacji **Native Application**.
- **Grant types**: *Authorization Code* oraz **Refresh Token**. KeyEnroll prosi
  o `offline_access`; bez grantu Refresh Token logowanie się nie powiedzie.
- **Sign-in redirect URI** z portem, domyślnie
  `http://localhost:8080/yubienroll-redirect`.
- **Assignments**: przypisz aplikację operatorom (albo grupie, do której należą).
  Operator bez przypisania nie zaloguje się do KeyEnroll.
- Na karcie **Okta API Scopes** **nadaj** (*Grant*) `okta.users.read`
  i `okta.users.manage`. KeyEnroll prosi o te dwa zakresy razem z `openid`
  i `offline_access`.

Administrator konfigurujący potrzebuje roli *Super Administrator* albo *Application
Administrator*.

### Operator

- Jedna z ról wymienionych przez Yubico: **Super Administrator**, **Organization
  Administrator** albo **Group Administrator**. Group Administrator ma dostęp tylko
  do użytkowników grup, którymi administruje.
- Okta przyznaje **część wspólną** zakresów aplikacji i roli operatora: same zakresy
  nie dają żadnych praw kontu, którego rola nie pozwala zarządzać metodami
  uwierzytelniania użytkowników. Innych ról, w tym własnych, nie sprawdzano.

### Ustawienia tenanta

- Organizacja w wersji **Okta Identity Engine**; tę wersję Yubico wymienia jako
  obsługiwaną. Classic Engine nie był sprawdzany.
- Metoda **FIDO2 (WebAuthn)** jest dodana i aktywna w *Security → Authenticators*.
  Żeby użytkownicy mogli logować się kluczem, polityki rejestracji metod
  uwierzytelniania i logowania muszą im na to pozwalać.

### Użytkownicy

- Konto istnieje w Okta.
- Wyszukiwarka w KeyEnroll znajduje użytkowników po imieniu, nazwisku albo adresie
  e-mail. Na [liście masowej](bulk.md) podaj jednak **nazwę użytkownika (login)**
  albo identyfikator użytkownika: tam Okta nie wyszukuje po adresie e-mail. Nazwa
  użytkownika często, ale nie zawsze, jest adresem e-mail.

### Warto wiedzieć

- Klucz bezpieczeństwa jest rejestrowany **dla jednej domeny**. Klucz zarejestrowany
  przez `example.okta.com` nie działa na własnej domenie tej samej organizacji —
  i odwrotnie. Wpisz domenę, na której użytkownicy faktycznie się logują; jeśli
  korzystają z obu, rejestruj przez dwie instancje.
- Okta sama nadaje kluczowi nazwę na podstawie modelu. Pole *Nazwa wyświetlana
  klucza* jest ignorowane.
- Podczas logowania port 8080 na Twoim komputerze musi być wolny.
- Źródło: [Yubico: Okta](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-okta.html).

## PingOne PingID

| Pole | Co wpisać |
|---|---|
| **Environment ID** | Identyfikator środowiska PingOne. |
| **Client ID** | Aplikacji utworzonej na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:9443/yubienroll-callback`. |
| **Region** | Region środowiska PingOne: Ameryka Północna, Europa, Kanada, Azja i Pacyfik, Australia lub Singapur. |
| **Własna domena** | Opcjonalnie. Tylko jeśli środowisko korzysta z własnej domeny. |
| **ID polityki MFA** | Opcjonalnie. Zostaw puste, żeby użyć domyślnej polityki MFA. |

### Aplikacja

- Typ aplikacji **Worker**, tak jak w instrukcji Yubico.
- Na karcie *Configuration*, w sekcji *OIDC Settings*:
    - **Response type** *Code*; **grant types** *Authorization Code* i *Refresh
      Token*;
    - **PKCE Enforcement** `S256_REQUIRED`;
    - **Token Endpoint Authentication Method** *None*;
    - **Redirect URI** z portem, domyślnie `http://localhost:9443/yubienroll-callback`.
- Włącz aplikację (przełącznik na liście aplikacji).

KeyEnroll prosi wyłącznie o `openid`. To, co może zrobić w API PingOne, wynika z ról
operatora, więc dodatkowe zakresy ani zasoby nie są potrzebne.

### Operator

- Role **Identity Data Admin** i **Environment Admin**, zgodnie z Yubico, nadane dla
  środowiska, w którym są użytkownicy.

### Ustawienia środowiska

- Środowisko ma **PingOne MFA** (PingID).
- Istnieje **polityka FIDO2** i jest częścią **polityki MFA** używanej przez
  KeyEnroll: domyślnej polityki MFA środowiska albo tej, której ID wpiszesz
  w instancji. Polityka FIDO2 decyduje o tym, które klucze są akceptowane (atestacja,
  dozwolone modele).
- Jeśli użytkownicy logują się na **własnej domenie**, wpisz ją w instancji, żeby
  klucz został zarejestrowany dla tej domeny.

### Użytkownicy

- Konto istnieje w środowisku PingOne, na które wskazuje instancja.

### Warto wiedzieć

- Podczas logowania port 9443 na Twoim komputerze musi być wolny.
- Źródło: [Yubico: PingOne PingID](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-pingone.html).

## PingOne Advanced Identity Cloud

| Pole | Co wpisać |
|---|---|
| **Tenant** | Nazwa hosta tenanta, np. `openam-example.forgeblocks.com`. |
| **Realm** | Domyślnie `alpha`. |
| **Nazwa journey** | Journey rejestracji WebAuthn utworzona na potrzeby rejestracji kluczy. |
| **Client ID** | Klienta OAuth 2.0 utworzonego na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:8443/yubienroll-redirect`. |
| **Origin WebAuthn** | Opcjonalnie. Zostaw puste, żeby użyć adresu tenanta. |

### Klient OAuth 2.0

- *Applications → Custom application*, **OIDC - OpenID Connect**, typ
  **Native / SPA**; **Token Endpoint Authentication Method** *None* (klient
  publiczny).
- **Grant types** *Authorization Code* i *Refresh Token*.
- **Zakresy** `openid`, `profile`, `fr:idm:*` (w *Show advanced settings*).
- **Redirect URI** z portem, domyślnie `http://localhost:8443/yubienroll-redirect`.
- Zarejestrowany w tym samym **realmie** co journey.

### Journey rejestracji

KeyEnroll prowadzi journey, która rejestruje klucz. Musi ona wyglądać tak:

1. **Jedno pytanie o nazwę użytkownika** (*Page Node* z *Platform Username* albo
   *Username Collector*). KeyEnroll odpowiada na nie wartością `userName`
   użytkownika.
2. Dalej wyłącznie **węzły po stronie serwera**, np. *Identify Existing User*,
   *Scripted Decision Node* albo *Inner Tree Evaluator*. Każde kolejne pytanie
   sprawia, że rejestracja się nie powiedzie.
3. **WebAuthn Registration Node** z **wyłączoną** opcją **Return challenge as
   JavaScript** oraz ustawieniami relying party ID i atestacji właściwymi dla Twojego
   środowiska.
4. *Success Node*; nieudane kontrole prowadzą do *Failure Node*.

Journey należy do realmu wpisanego w instancji.

!!! warning "Niech journey sprawdza, kto rejestruje klucz"
    Journey jest dostępna pod publicznym adresem logowania tenanta. Bez kroku
    autoryzacji każdy, kto może ją uruchomić, mógłby zarejestrować klucz dla dowolnej
    nazwy użytkownika. Dlatego KeyEnroll wysyła token dostępu operatora przy każdym
    wywołaniu journey, a instrukcja Yubico dodaje **Scripted Decision Node**, który
    sprawdza ten token (introspekcja) i to, czy operator należy do uprawnionej grupy
    (w przykładzie `webauthn-admins`). Skrypt potrzebuje osobnego klienta OAuth 2.0
    z zakresem `am-introspect-all-tokens`, którego identyfikator i sekret są
    przechowywane w ESV (`esv.yubienroll.introspect.client.id`,
    `esv.yubienroll.introspect.client.secret`, `esv.yubienroll.tenant`). Realm
    w skrypcie musi zgadzać się z Twoim.

### Operator

- Rola wewnętrzna **`openidm-admin`**: KeyEnroll wyszukuje użytkowników przez API
  zarządzania tożsamościami (`fr:idm:*`).
- To, co sprawdza krok autoryzacji w journey, np. członkostwo w `webauthn-admins`.

### Użytkownicy

- Konto istnieje jako zarządzany użytkownik realmu (`<realm>_user`) z wartością
  `userName`, którą KeyEnroll wysyła do journey.

### Ograniczenia

Ten dostawca nie udostępnia interfejsu do listowania ani usuwania poświadczeń, więc
strona [Poświadczenia](credentials.md) jest niedostępna. Zarządzaj nimi w konsoli
administracyjnej.

Źródło: [Yubico: PingOne AIC](https://docs.yubico.com/software/yubikey/tools/yubienroll/yubienroll-pingone-aic.html).

## Listy masowe z grup { #bulk-lists-from-groups }

!!! info "Od wersji 0.7.0"

[Wczytanie listy z grupy](bulk.md#loading-the-list-from-a-group) odczytuje członkostwo
w grupach, na co nie pozwala rejestracja opisana przez YubiEnroll. Dlatego opcja jest
**wyłączona**, dopóki nie włączysz jej dla instancji:

1. Nadaj dodatkowe uprawnienie u dostawcy tożsamości (tabela poniżej).
2. W KeyEnroll edytuj instancję i ustaw **Listy masowe z grup** na **Włączone**.
3. **Wyloguj się i zaloguj ponownie**, żeby nowe uprawnienie weszło do logowania.

| Dostawca tożsamości | Dodatkowe uprawnienie |
|---|---|
| Microsoft Entra ID | Delegowane uprawnienie Microsoft Graph `GroupMember.Read.All` ze zgodą administratora dla tenanta. |
| Okta | Zakres `okta.groups.read`, nadany aplikacji na karcie *Okta API Scopes*. |
| PingOne PingID | Bez zakresu; rola operatora musi pozwalać na odczyt grup. *Identity Data Admin*, potrzebna i tak do rejestracji, to obejmuje; operator z węższą rolą potrzebuje dodatkowo *Identity Data Read Only*. |
| PingOne Advanced Identity Cloud | Bez zmian; `fr:idm:*` obejmuje już grupy. Grupy są odczytywane z obiektu `<realm>_group`, a ich członkowie przez relację `groups` użytkowników. **Jeszcze niesprawdzone na żywym tenancie**: jeśli w Twoim tenancie nie działa, prosimy o [zgłoszenie](https://github.com/inowakowski/KeyEnroll/issues). |

Jeśli opcja jest włączona, a uprawnienia brakuje, logowanie lub wczytanie grupy
kończy się komunikatem dostawcy o braku zgody albo zabronionym żądaniu.

## Czy to było testowane?

Na żywym tenancie potwierdzono dotąd tylko integrację z **Okta**. Pozostałe trzy
zostały zaimplementowane na podstawie publicznej dokumentacji API dostawców i są
objęte testami automatycznymi na symulowanych odpowiedziach; możliwe, że jakiś
szczegół będzie wymagał poprawki — prosimy wtedy o
[zgłoszenie](https://github.com/inowakowski/KeyEnroll/issues).

Wymagania opisane na tej stronie pochodzą z instrukcji YubiEnroll firmy Yubico
i z dokumentacji samych dostawców (stan z października 2026). Dostawcy co jakiś czas
zmieniają nazwy menu i ról; jeśli coś tutaj nie zgadza się już z Twoją konsolą,
prosimy o [zgłoszenie](https://github.com/inowakowski/KeyEnroll/issues).
