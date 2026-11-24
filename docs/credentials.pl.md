# Poświadczenia

Strona **Poświadczenia** pokazuje, jakie klucze FIDO użytkownik ma zarejestrowane
u dostawcy tożsamości, i pozwala usunąć wybrany — na przykład gdy klucz zaginął albo
pracownik go zwrócił.

![Strona Poświadczenia](assets/screenshots/pl/credentials.png){ .shot }

## Strona

**Użytkownik** (u góry). Po otwarciu strony widać **wszystkich użytkowników**
katalogu, posortowanych po nazwie, więc wyszukiwanie jest opcjonalne: zaznacz
użytkownika na liście albo zawęź ją wyszukiwarką, tak jak na
[stronie Rejestracja](enroll.md#1-user). **Odśwież listę** czyści wyszukiwanie
i wczytuje użytkowników ponownie; zaznaczony użytkownik pozostaje zaznaczony. Puste
wyszukiwanie też pokazuje wszystkich. Przy bardzo dużych katalogach widać pierwszych
5000 użytkowników; pozostałych znajdziesz wyszukiwarką.

Gdy Okta [przechowuje numery seryjne](providers.md#key-serial-numbers), po
podłączeniu YubiKeya u góry strony pojawia się wyróżniony baner z informacją, do kogo
klucz należy, np. *Podłączony klucz S/N 32445513 należy do: Alicja Przykład*.
**Pokaż klucze użytkownika** zaznacza tego użytkownika, a poświadczenie
z podłączonego klucza zostaje zaznaczone, gotowe do usunięcia. Ten sam baner na
[stronie Rejestracja](enroll.md) przenosi tutaj.

**Poświadczenia FIDO wybranego użytkownika** (na dole)

| Kolumna | Znaczenie |
|---|---|
| **Nazwa** | Nazwa, pod którą klucz został zarejestrowany. |
| **Numer seryjny** | W Okcie, gdy instancja [zapisuje numery seryjne](providers.md#key-serial-numbers). W pozostałych przypadkach puste. |
| **Utworzono** | Kiedy został zarejestrowany. |
| **Szczegóły** | Co dostawca wie o kluczu, zwykle jego model. |
| **ID** | Identyfikator poświadczenia u dostawcy. |

| Przycisk | Do czego służy |
|---|---|
| **Odśwież** | Odczytuje listę ponownie. |
| **Usuń zaznaczone** | Po potwierdzeniu usuwa zaznaczone poświadczenie z konta użytkownika. |

!!! danger "Usunięcia nie da się cofnąć"
    Po usunięciu poświadczenia użytkownik od razu traci możliwość logowania tym
    kluczem. Żeby znów go używać, klucz trzeba zarejestrować od nowa. Usunięcie
    tutaj nie zmienia niczego na samym kluczu: jego PIN i pozostałe poświadczenia
    zostają.

## Co obsługują dostawcy

| Dostawca tożsamości | Lista | Usuwanie |
|---|---|---|
| Microsoft Entra ID | tak | tak |
| Okta | tak | tak |
| PingOne PingID | tak | tak |
| PingOne Advanced Identity Cloud | nie | nie |

PingOne Advanced Identity Cloud nie udostępnia do tego interfejsu; poświadczeniami
zarządza się w jego konsoli administracyjnej. Strona informuje o tym, gdy wybrana
jest taka instancja.
