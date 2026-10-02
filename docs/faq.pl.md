# Częste pytania

## Czy KeyEnroll to oficjalny produkt Yubico?

Nie. To niezależny projekt open source, niepowiązany z firmami Yubico, Microsoft,
Okta ani Ping Identity i przez nie niewspierany. Powstał, bo narzędzie YubiEnroll
firmy Yubico jest programem wiersza poleceń tylko dla Windows.

## Czy trzeba mieć zainstalowany YubiEnroll?

Nie. KeyEnroll w ogóle nie korzysta z YubiEnroll. Używa jedynie tej samej
*rejestracji aplikacji* u dostawcy tożsamości, którą opisuje dokumentacja YubiEnroll.

## Jak to może działać na macOS i Linuksie, skoro YubiEnroll tam nie działa?

Z kluczem rozmawia otwarta biblioteka python-fido2 — ta sama, na której Yubico
opiera własne narzędzia dla macOS i Linuksa — a rejestracja klucza u dostawcy
tożsamości to seria zwykłych żądań HTTPS. Protokół, którym rozmawia się z kluczem,
jest identyczny w każdym systemie; różni się tylko sposób otwarcia urządzenia USB.

To uzasadnione oczekiwanie, a nie potwierdzony fakt: w chwili pisania tych słów
nikt nie zgłosił rejestracji klucza paczką dla macOS lub Linuksa. Zobacz
[co zostało sprawdzone](index.md#what-has-been-tested).

## Jakie klucze działają?

Każdy klucz FIDO2 da się zresetować, zabezpieczyć PIN-em i zarejestrować. Numer
seryjny i wersja firmware są odczytywane z kluczy YubiKey. Opcje takie jak minimalna
długość PIN-u, wymuszona zmiana PIN-u i „zawsze wymagaj UV” wymagają klucza
z nowszym firmware; zobacz [Profile](profiles.md#what-the-key-has-to-support).

## Dlaczego Windows za każdym razem pyta o uprawnienia administratora?

Windows zastrzega bezpośredni dostęp do kluczy FIDO dla procesów z podniesionymi
uprawnieniami. Zwykłe programy muszą korzystać z okien Windows Hello, które nie
potrafią zresetować klucza ani ustawić jego opcji. To cecha Windows, nie KeyEnroll.

## Dlaczego Windows i macOS ostrzegają przy instalacji?

Instalatory nie są podpisane cyfrowo, bo certyfikaty do podpisywania kodu i konto
dewelopera Apple kosztują. Kod źródłowy i skrypty budujące są publiczne,
a instalatory budują z nich serwery GitHuba. Zobacz [Instalacja](install.md).

## Czy KeyEnroll widzi moje hasło administratora?

Nie. Logujesz się na stronie dostawcy tożsamości w swojej przeglądarce. KeyEnroll
dostaje token, który pozwala mu działać w Twoim imieniu, i przechowuje go
w systemowym magazynie poświadczeń.

## Gdzie jest zapisany PIN? Czy da się go później sprawdzić?

Nigdzie — i nie da się. PIN jest pokazywany raz, po rejestracji, a na liście
wdrożenia masowego pozostaje, dopóki działa aplikacja. Jeśli przepadnie, klucz
trzeba zarejestrować ponownie z resetem fabrycznym.

## Czy użytkownik może zmienić PIN?

Tak, w każdej chwili, narzędziami systemu operacyjnego (np. *Opcje logowania → Klucz
zabezpieczeń* w ustawieniach Windows) albo programem Yubico Authenticator. Przy
opcji *Wymuś zmianę PIN-u przed pierwszym użyciem* musi to zrobić przy pierwszym
użyciu klucza.

## Czy można zarejestrować kilka kluczy dla jednego użytkownika?

Tak. Rejestruj je jeden po drugim i nadawaj nazwy, które pozwolą je odróżnić — na
przykład z numerem seryjnym. Dostawcy tożsamości ograniczają liczbę kluczy na
użytkownika.

## Czy jeden klucz może służyć kilku użytkownikom lub tenantom?

Klucz może przechowywać poświadczenia wielu kont. Dla drugiego konta zarejestruj go
**bez resetu fabrycznego**, w przeciwnym razie pierwsze poświadczenie zostanie
usunięte.

## Czy aplikacja wysyła jakieś dane autorowi?

Nie. Nie ma telemetrii. Jedyne połączenie poza Twoim dostawcą tożsamości to
sprawdzanie aktualizacji — i tylko po kliknięciu przycisku. Zobacz
[Dane i bezpieczeństwo](data.md#what-keyenroll-communicates-with).

## Jakie języki są dostępne?

Aplikacja: polski, angielski, niemiecki, hiszpański, francuski i włoski. Ta
dokumentacja: polski i angielski.

## Mam błąd do zgłoszenia albo brakuje mi funkcji.

Otwórz zgłoszenie na [stronie projektu](https://github.com/inowakowski/KeyEnroll/issues).
Opisz, co zostało zrobione i co się stało, podaj wersję, system operacyjny
i dostawcę tożsamości. Zobacz
[Zgłaszanie problemu](troubleshooting.md#reporting-a-problem).

## Czy mogę używać aplikacji w firmie? Czy mogę ją modyfikować?

Tak, jedno i drugie. KeyEnroll jest udostępniany na licencji MIT: można go używać
za darmo, także komercyjnie, modyfikować i rozpowszechniać pod warunkiem zachowania
tekstu licencji. Jest dostarczany bez gwarancji. Dołączone biblioteki mają własne
licencje, wymienione w pliku `THIRD-PARTY-NOTICES.md` w każdej paczce.
