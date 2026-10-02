# Dostawcy tożsamości

Przed pierwszym logowaniem u dostawcy tożsamości trzeba **zarejestrować aplikację**.
Dzięki niej dostawca wie, że KeyEnroll może logować administratorów i w ich imieniu
zarządzać kluczami bezpieczeństwa użytkowników.

KeyEnroll korzysta z **tej samej rejestracji co narzędzie YubiEnroll firmy Yubico**.
Yubico publikuje dla każdego dostawcy instrukcję krok po kroku ze zrzutami ekranu
(po angielsku); wykonaj ją, a otrzymane wartości wpisz w [instancji](instances.md)
KeyEnroll:

[YubiEnroll: konfiguracja dostawców tożsamości](https://docs.yubico.com/software/yubikey/tools/yubienroll/index-idp.html){ .md-button }

Ta strona wymienia dla każdego dostawcy pola, o które pyta KeyEnroll, to, o co
aplikacja prosi dostawcę, oraz miejsca, w których najczęściej coś idzie nie tak.

!!! info "Wspólne dla wszystkich dostawców"
    - Aplikację rejestruje się jako **klienta publicznego (natywnego)** z przepływem
      *authorization code* i PKCE. KeyEnroll nie przechowuje żadnego sekretu klienta.
    - **Redirect URI** musi zaczynać się od `http://localhost` i dokładnie zgadzać
      się z rejestracją. Podczas logowania KeyEnroll nasłuchuje pod tym adresem
      wyłącznie na Twoim komputerze.
    - Domyślne redirect URI nadal zawierają słowo `yubienroll`, żeby rejestracja
      wykonana dla YubiEnroll działała bez zmian. Jeśli zarejestrujesz inny adres,
      wpisz taki sam w instancji.

## Microsoft Entra ID

| Pole | Co wpisać |
|---|---|
| **Identyfikator katalogu (tenant ID)** | Ze strony *Przegląd* rejestracji aplikacji. |
| **Identyfikator aplikacji (client ID)** | Z tej samej strony. |
| **Redirect URI** | Domyślnie `http://localhost/yubienroll-redirect`. |
| **Punkt końcowy Entra ID** | Zostaw `https://login.microsoftonline.com`. Zmień tylko dla chmur krajowych. |
| **Punkt końcowy Microsoft Graph** | Zostaw `https://graph.microsoft.com`. Zmień tylko dla chmur krajowych. |

**Uprawnienia, o które prosi aplikacja** (delegowane, Microsoft Graph):
`User.ReadBasic.All` i `UserAuthenticationMethod.ReadWrite.All`. Administrator musi
udzielić zgody dla tenanta.

**Rola zalogowanego administratora:** *Authentication Administrator* albo
*Privileged Authentication Administrator*, jeśli ma zarządzać kluczami innych
administratorów.

**Sprawdź w tenancie:**

- W *Metody uwierzytelniania → Passkey (FIDO2)* metoda jest włączona dla danych
  użytkowników i włączona jest opcja **Allow self-service setup**.
- Jeśli polityka ogranicza klucze według AAGUID lub wymusza atestację, wydawane
  klucze muszą ją spełniać.

**Warto wiedzieć:** nazwa klucza jest ograniczona do 30 znaków.

## Okta

| Pole | Co wpisać |
|---|---|
| **Domena Okta** | Na przykład `example.okta.com` albo własna domena. |
| **Client ID** | Aplikacji utworzonej na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:8080/yubienroll-redirect`. |

**Zakresy, o które prosi aplikacja:** `openid`, `offline_access`, `okta.users.read`,
`okta.users.manage`. Oba zakresy API Okta trzeba przyznać aplikacji.

**Rola zalogowanego administratora:** taka, która pozwala zarządzać użytkownikami
i ich metodami uwierzytelniania.

**Warto wiedzieć:**

- Klucz bezpieczeństwa jest rejestrowany **dla jednej domeny**. Klucz zarejestrowany
  przez `example.okta.com` nie działa na własnej domenie tej samej organizacji —
  i odwrotnie. Wpisz domenę, na której użytkownicy faktycznie się logują.
- Okta sama nadaje kluczowi nazwę na podstawie modelu. Pole *Nazwa wyświetlana
  klucza* jest ignorowane.
- Podczas logowania port 8080 na Twoim komputerze musi być wolny.

## PingOne PingID

| Pole | Co wpisać |
|---|---|
| **Environment ID** | Identyfikator środowiska PingOne. |
| **Client ID** | Aplikacji utworzonej na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:9443/yubienroll-callback`. |
| **Region** | Region środowiska PingOne: Ameryka Północna, Europa, Kanada, Azja i Pacyfik, Australia lub Singapur. |
| **Własna domena** | Opcjonalnie. Tylko jeśli środowisko korzysta z własnej domeny. |
| **ID polityki MFA** | Opcjonalnie. Zostaw puste, żeby użyć domyślnej polityki MFA. |

**Rola zalogowanego administratora:** taka, która pozwala odczytywać użytkowników
i zarządzać ich urządzeniami MFA w środowisku.

**Warto wiedzieć:** o tym, które klucze są akceptowane, decyduje polityka FIDO
środowiska.

## PingOne Advanced Identity Cloud

| Pole | Co wpisać |
|---|---|
| **Tenant** | Nazwa hosta tenanta, np. `openam-example.forgeblocks.com`. |
| **Realm** | Domyślnie `alpha`. |
| **Nazwa journey** | Journey rejestracji WebAuthn utworzona na potrzeby rejestracji kluczy. |
| **Client ID** | Klienta OAuth 2.0 utworzonego na potrzeby rejestracji. |
| **Redirect URI** | Domyślnie `http://localhost:8443/yubienroll-redirect`. |
| **Origin WebAuthn** | Opcjonalnie. Zostaw puste, żeby użyć adresu tenanta. |

**Zakresy, o które prosi aplikacja:** `openid`, `profile`, `fr:idm:*`.

**Sprawdź w tenancie:**

- W węźle *WebAuthn Registration Node* tej journey opcja **Return challenge as
  JavaScript** jest **wyłączona**.

**Ograniczenia:** ten dostawca nie udostępnia interfejsu do listowania ani usuwania
poświadczeń, więc strona [Poświadczenia](credentials.md) jest niedostępna. Zarządzaj
nimi w konsoli administracyjnej.

## Czy to było testowane?

Na żywym tenancie potwierdzono dotąd tylko integrację z **Okta**. Pozostałe trzy
zostały zaimplementowane na podstawie publicznej dokumentacji API dostawców i są
objęte testami automatycznymi na symulowanych odpowiedziach; możliwe, że jakiś
szczegół będzie wymagał poprawki — prosimy wtedy o
[zgłoszenie](https://github.com/inowakowski/KeyEnroll/issues).
