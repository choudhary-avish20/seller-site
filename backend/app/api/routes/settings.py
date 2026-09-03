from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_seller_or_admin
from app.db.session import get_db
from app.models.site_settings import SiteSettings
from app.models.user import User
from app.schemas.settings import SiteSettingsResponse, SiteSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

# Starter Terms & Conditions text (Polish, B2B wholesale, COD-only payment,
# delivery by the seller's own courier — matches this store's actual model).
# Every bracketed [PLACEHOLDER] must be filled in with the real registered
# business details by an admin (Panel → Regulamin) before this is relied on
# as a binding legal document; it is a starting template, not legal advice.
_DEFAULT_TERMS = """REGULAMIN SKLEPU HURTOWEGO [NAZWA SKLEPU]

Niniejszy Regulamin określa zasady korzystania ze sklepu internetowego [NAZWA SKLEPU] (dalej: „Sklep”), dostępnego pod adresem [ADRES STRONY], oraz zasady zawierania i realizacji umów sprzedaży hurtowej za jego pośrednictwem.

§1. Postanowienia ogólne

1. Sklep prowadzony jest przez: [IMIĘ I NAZWISKO / PEŁNA NAZWA FIRMY], z siedzibą pod adresem: [ADRES SIEDZIBY], NIP: [NIP], REGON: [REGON], wpisaną do [CEIDG / Krajowego Rejestru Sądowego pod numerem KRS: ...] (dalej: „Sprzedawca”).
2. Kontakt ze Sprzedawcą możliwy jest pod adresem e-mail: [E-MAIL KONTAKTOWY] oraz numerem telefonu: [NUMER TELEFONU].
3. Sklep prowadzi sprzedaż hurtową wyłącznie na rzecz przedsiębiorców w rozumieniu art. 43[1] Kodeksu cywilnego, dokonujących zakupu w związku z prowadzoną działalnością gospodarczą lub zawodową (sprzedaż B2B). Sklep nie prowadzi sprzedaży detalicznej na rzecz konsumentów.
4. Warunkiem korzystania ze Sklepu jest akceptacja niniejszego Regulaminu oraz podanie prawdziwych danych identyfikujących prowadzoną działalność gospodarczą (nazwa firmy, adres, NIP).

§2. Definicje

1. Sklep — platforma internetowa prowadzona przez Sprzedawcę, umożliwiająca składanie zamówień hurtowych.
2. Kupujący — przedsiębiorca zakładający konto i składający zamówienia w Sklepie.
3. Konto — indywidualne konto Kupującego w Sklepie, założone po weryfikacji adresu e-mail.
4. Towar — produkty oferowane do sprzedaży hurtowej w Sklepie, sprzedawane w opakowaniach zbiorczych (paczkach) zgodnie z podanym rozmiarem opakowania i wielokrotnością zamówienia.
5. Zamówienie — oświadczenie woli Kupującego zmierzające do zawarcia umowy sprzedaży Towarów, złożone za pośrednictwem Sklepu.

§3. Warunki techniczne korzystania ze Sklepu

1. Do korzystania ze Sklepu niezbędne są: urządzenie z dostępem do sieci Internet, aktualna przeglądarka internetowa oraz aktywny adres e-mail.
2. Sprzedawca dokłada starań, aby Sklep działał w sposób ciągły, jednak nie gwarantuje nieprzerwanej dostępności i zastrzega możliwość czasowych przerw technicznych.
3. Reklamacje dotyczące funkcjonowania Sklepu (usługi świadczonej drogą elektroniczną) można zgłaszać na adres e-mail wskazany w §1 ust. 2. Sprzedawca rozpatruje takie zgłoszenia w terminie do 14 dni.

§4. Rejestracja i konto Kupującego

1. Założenie Konta wymaga podania danych firmy (nazwa, NIP), danych kontaktowych oraz potwierdzenia adresu e-mail za pomocą linku aktywacyjnego.
2. Sprzedawca może uzależnić możliwość składania Zamówień od dodatkowej weryfikacji statusu przedsiębiorcy.
3. Kupujący zobowiązany jest do podawania danych zgodnych z prawdą i ich aktualizacji w razie zmian.
4. Kupujący ponosi odpowiedzialność za zachowanie poufności danych logowania do Konta.

§5. Asortyment, ceny i minimalne ilości zamówienia

1. Ceny Towarów podawane są w złotych polskich (PLN), w wartości netto i brutto (z uwzględnieniem podatku VAT według obowiązującej stawki).
2. Towary sprzedawane są wyłącznie w pełnych opakowaniach zbiorczych (paczkach) oraz w wielokrotności wskazanego przy danym Towarze minimalnego przyrostu zamówienia (MOQ). Zamówienie niespełniające tego warunku nie zostanie przyjęte do realizacji.
3. Dla wybranych Towarów mogą obowiązywać progi cenowe uzależnione od zamawianej ilości, wskazane każdorazowo na stronie produktu.
4. Sprzedawca zastrzega sobie prawo do zmiany cen i dostępności Towarów; zmiany te nie dotyczą Zamówień już przyjętych do realizacji.

§6. Składanie i realizacja Zamówień

1. Zamówienia mogą składać wyłącznie zalogowani Kupujący posiadający potwierdzony adres e-mail.
2. Złożenie Zamówienia następuje poprzez dodanie Towarów do koszyka, podanie danych dostawy i danych do faktury (nazwa firmy, NIP — o ile dotyczy) oraz potwierdzenie Zamówienia.
3. Umowę sprzedaży uważa się za zawartą z chwilą potwierdzenia przyjęcia Zamówienia do realizacji przez Sprzedawcę. Do tego momentu Sprzedawca może odmówić realizacji Zamówienia, w szczególności w przypadku braku dostępności Towaru.
4. Sprzedawca przesyła potwierdzenie złożenia Zamówienia oraz informacje o zmianie jego statusu na adres e-mail Kupującego.

§7. Płatność

1. Jedyną dostępną formą płatności w Sklepie jest płatność gotówką za pobraniem (COD) — Kupujący płaci należność bezpośrednio kurierowi Sprzedawcy w momencie odbioru Towaru.
2. Sklep nie przyjmuje przedpłat ani płatności elektronicznych za pośrednictwem Sklepu.
3. Do każdego Zamówienia Sprzedawca dołącza dokument sprzedaży (fakturę lub paragon) zgodnie z danymi podanymi przez Kupującego.

§8. Dostawa

1. Dostawa Towarów realizowana jest własnym transportem Sprzedawcy — Sprzedawca nie korzysta z zewnętrznych firm kurierskich.
2. Orientacyjny termin dostawy wskazywany jest po potwierdzeniu Zamówienia i zależy od dostępności Towaru oraz lokalizacji dostawy.
3. Kupujący zobowiązany jest zapewnić możliwość odbioru Towaru pod wskazanym adresem w uzgodnionym terminie. W przypadku nieudanej próby doręczenia z przyczyn leżących po stronie Kupującego, koszt ponownej dostawy może zostać przeniesiony na Kupującego.
4. Z chwilą wydania Towaru Kupującemu (lub osobie przez niego upoważnionej do odbioru) na Kupującego przechodzą korzyści i ciężary związane z Towarem oraz niebezpieczeństwo przypadkowej utraty lub uszkodzenia.

§9. Odbiór Towaru i reklamacje (rękojmia)

1. Kupujący zobowiązany jest sprawdzić stan przesyłki oraz zgodność Towaru z Zamówieniem w obecności kuriera w momencie odbioru.
2. Ewentualne niezgodności ilościowe, uszkodzenia powstałe w transporcie lub wady jawne Towaru należy zgłosić kurierowi przy odbiorze oraz Sprzedawcy niezwłocznie, nie później niż w terminie 3 dni roboczych od dnia dostawy, na adres e-mail wskazany w §1 ust. 2.
3. Wady ukryte Towaru należy zgłosić niezwłocznie po ich wykryciu, nie później niż w terminie 7 dni od dnia ich ujawnienia.
4. Z uwagi na to, że sprzedaż w Sklepie odbywa się wyłącznie pomiędzy przedsiębiorcami, na podstawie art. 558 § 1 Kodeksu cywilnego strony ograniczają odpowiedzialność Sprzedawcy z tytułu rękojmi do zasad opisanych w niniejszym paragrafie; Kupującemu nie przysługuje ustawowe prawo odstąpienia od umowy zawartej na odległość przewidziane dla konsumentów.
5. Sprzedawca rozpatruje zgłoszenia reklamacyjne w terminie do 14 dni od ich otrzymania i informuje Kupującego o sposobie ich rozpatrzenia na adres e-mail podany w Zamówieniu.

§10. Dane osobowe

1. Administratorem danych osobowych Kupujących (osób reprezentujących Kupującego) jest Sprzedawca wskazany w §1 ust. 1.
2. Dane osobowe przetwarzane są w celu założenia i obsługi Konta, realizacji Zamówień, wystawienia dokumentów sprzedaży oraz wypełnienia obowiązków prawnych (w tym podatkowych) ciążących na Sprzedawcy — na podstawie art. 6 ust. 1 lit. b) i c) RODO.
3. Osobie, której dane dotyczą, przysługuje prawo dostępu do danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, przenoszenia oraz wniesienia sprzeciwu, a także prawo wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych.
4. Szczegółowa Polityka Prywatności, opisująca zasady przetwarzania danych osobowych i wykorzystania plików cookies, zostanie opublikowana odrębnie pod adresem [ADRES POLITYKI PRYWATNOŚCI].

§11. Własność intelektualna

1. Treści zamieszczone w Sklepie (w tym opisy, zdjęcia, elementy graficzne i logotypy) stanowią własność Sprzedawcy lub są wykorzystywane przez niego na podstawie odpowiednich licencji i podlegają ochronie prawnej.
2. Kopiowanie, rozpowszechnianie lub wykorzystywanie tych treści bez zgody Sprzedawcy jest zabronione.

§12. Postanowienia końcowe

1. Sprzedawca zastrzega sobie prawo do zmiany niniejszego Regulaminu z ważnych przyczyn (w tym zmian przepisów prawa lub sposobu funkcjonowania Sklepu). Zmiany nie mają wpływu na Zamówienia złożone przed ich wejściem w życie.
2. Aktualna wersja Regulaminu jest zawsze dostępna na stronie Sklepu.
3. W sprawach nieuregulowanych niniejszym Regulaminem zastosowanie mają przepisy prawa polskiego, w szczególności Kodeksu cywilnego.
4. Wszelkie spory wynikłe na tle wykonywania umów sprzedaży podlegają rozstrzygnięciu przez sąd właściwy dla siedziby Sprzedawcy.
5. Jeżeli którekolwiek postanowienie Regulaminu zostanie uznane za nieważne lub bezskuteczne, pozostałe postanowienia pozostają w mocy.

Regulamin obowiązuje od dnia: [DATA WEJŚCIA W ŻYCIE].

—
Niniejszy dokument jest szablonem przygotowanym jako punkt wyjścia i wymaga uzupełnienia danych oznaczonych nawiasami kwadratowymi oraz weryfikacji przez radcę prawnego lub adwokata przed jego opublikowaniem jako obowiązującego regulaminu."""

# Starter Privacy Policy (RODO/GDPR-shaped). Same caveat as the Terms above —
# a template requiring real business details and legal review, not legal advice.
_DEFAULT_PRIVACY = """POLITYKA PRYWATNOŚCI SKLEPU [NAZWA SKLEPU]

§1. Administrator danych osobowych

Administratorem danych osobowych zbieranych za pośrednictwem sklepu internetowego dostępnego pod adresem [ADRES STRONY] jest [NAZWA FIRMY], z siedzibą pod adresem: [ADRES SIEDZIBY], NIP: [NIP] (dalej: „Administrator”). Kontakt w sprawach ochrony danych: [E-MAIL KONTAKTOWY].

§2. Zakres i cele przetwarzania danych

Administrator przetwarza dane osobowe Kupujących (imię i nazwisko, dane firmy, adres e-mail, numer telefonu, adres dostawy) w następujących celach:
1. Założenie i obsługa konta w Sklepie — na podstawie art. 6 ust. 1 lit. b) RODO (wykonanie umowy).
2. Realizacja i rozliczenie Zamówień, w tym wystawienie dokumentów sprzedaży — na podstawie art. 6 ust. 1 lit. b) i c) RODO (wykonanie umowy oraz obowiązki podatkowo-księgowe).
3. Obsługa reklamacji i korespondencji z Kupującym — na podstawie art. 6 ust. 1 lit. b) i f) RODO (prawnie uzasadniony interes Administratora).
4. Wysyłka wiadomości transakcyjnych (potwierdzenie zamówienia, zmiana statusu, weryfikacja adresu e-mail) — na podstawie art. 6 ust. 1 lit. b) RODO.

§3. Okres przechowywania danych

Dane osobowe przechowywane są przez okres niezbędny do realizacji celów wskazanych w §2, w tym przez okres wymagany przepisami prawa podatkowego i rachunkowego (co do dokumentów sprzedaży), a po tym okresie — do czasu przedawnienia ewentualnych roszczeń.

§4. Odbiorcy danych

Dane mogą być przekazywane podmiotom wspierającym Administratora w prowadzeniu Sklepu (np. dostawca hostingu, biuro rachunkowe) wyłącznie w zakresie niezbędnym do realizacji ich usług, na podstawie odpowiednich umów powierzenia przetwarzania danych. Administrator nie sprzedaje danych osobowych podmiotom trzecim.

§5. Prawa osób, których dane dotyczą

Każdej osobie, której dane są przetwarzane, przysługuje prawo do: dostępu do swoich danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, przenoszenia danych oraz wniesienia sprzeciwu wobec przetwarzania, a także prawo do wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych, jeśli uzna, że przetwarzanie narusza przepisy RODO.

§6. Pliki cookies

Sklep wykorzystuje pliki cookies w celu zapewnienia prawidłowego działania (np. utrzymania sesji zalogowanego Kupującego, zapamiętania zawartości koszyka) oraz — jeśli dotyczy — do celów statystycznych. Korzystając ze Sklepu, użytkownik może zarządzać ustawieniami cookies w swojej przeglądarce internetowej, w tym je zablokować, co może wpłynąć na działanie niektórych funkcji Sklepu.

§7. Bezpieczeństwo danych

Administrator stosuje odpowiednie środki techniczne i organizacyjne zapewniające bezpieczeństwo przetwarzanych danych osobowych, w tym ochronę przed nieuprawnionym dostępem, utratą lub zniszczeniem danych.

§8. Zmiany Polityki Prywatności

Administrator zastrzega sobie prawo do wprowadzania zmian w niniejszej Polityce Prywatności. Aktualna wersja jest zawsze dostępna na stronie Sklepu.

—
Niniejszy dokument jest szablonem przygotowanym jako punkt wyjścia i wymaga uzupełnienia danych oznaczonych nawiasami kwadratowymi oraz weryfikacji przez radcę prawnego lub adwokata przed jego opublikowaniem jako obowiązującej polityki prywatności."""

_DEFAULT_FAQ = """Najczęściej zadawane pytania

Czy mogę kupować jako osoba prywatna?
Nie — Sklep prowadzi sprzedaż wyłącznie dla firm (B2B). Przy rejestracji poprosimy o nazwę firmy i NIP.

Jak założyć konto?
Kliknij „Zarejestruj się", podaj dane firmy oraz adres e-mail. Na podany adres wyślemy link aktywacyjny — po jego potwierdzeniu możesz od razu przeglądać ceny i składać zamówienia.

Jakie są minimalne ilości zamówienia?
Każdy produkt sprzedawany jest w pełnych opakowaniach zbiorczych (paczkach) oraz w wielokrotności wskazanego przy produkcie przyrostu zamówienia — np. co 12 lub co 40 sztuk. Dokładne informacje znajdziesz na stronie każdego produktu.

Jak wygląda płatność?
Jedyną dostępną formą płatności jest płatność za pobraniem (COD) — płacisz gotówką kurierowi w momencie odbioru towaru.

Jak przebiega dostawa?
Dostawę realizujemy własnym transportem, bez pośrednictwa zewnętrznych firm kurierskich. Orientacyjny czas dostawy podajemy po potwierdzeniu zamówienia.

Czy mogę śledzić status zamówienia?
Tak — w zakładce „Moje zamówienia" widzisz aktualny status każdego zamówienia (Oczekujące, Potwierdzone, Wysłane, Zrealizowane).

Czy mogę anulować zamówienie?
Zamówienie o statusie „Oczekujące" możesz anulować samodzielnie w zakładce „Moje zamówienia". Zamówienia w trakcie realizacji prosimy zgłaszać do anulowania bezpośrednio do nas.

Co jeśli produkt jest wadliwy lub niezgodny z zamówieniem?
Sprawdź przesyłkę przy odbiorze — ewentualne uszkodzenia lub braki zgłoś kurierowi na miejscu oraz nam mailowo. Szczegóły procedury reklamacyjnej znajdziesz w Regulaminie.

Jak mogę się z Wami skontaktować?
Dane kontaktowe (telefon, e-mail, WhatsApp) znajdziesz na stronie Kontakt."""

_DEFAULT_SHIPPING = """Koszty i czas dostawy

Własny transport
Dostawę realizujemy własnym transportem — nie korzystamy z zewnętrznych firm kurierskich. Dzięki temu mamy pełną kontrolę nad jakością i terminowością dostaw.

Czas dostawy
Orientacyjny termin dostawy podawany jest po potwierdzeniu zamówienia przez naszego pracownika i zależy od bieżącej dostępności towaru oraz lokalizacji dostawy.

Koszt dostawy
Szczegółowy koszt dostawy ustalany jest indywidualnie w zależności od wielkości zamówienia i lokalizacji — informację otrzymasz przy potwierdzeniu zamówienia.

Płatność przy odbiorze
Płacisz gotówką bezpośrednio kierowcy w momencie dostawy (płatność za pobraniem — COD). Prosimy o przygotowanie odpowiedniej kwoty.

Odbiór towaru
Przy odbiorze prosimy o sprawdzenie zgodności przesyłki z zamówieniem oraz jej stanu w obecności kierowcy — wszelkie niezgodności najlepiej zgłosić od razu."""

# Sensible defaults so the public Contact page isn't empty before an admin
# fills in the real details — matches what was previously hardcoded in the UI.
_DEFAULTS = {
    "phone": "+48 579 383 945",
    "email": "kontakt@wolkago.pl",
    "address": "Wólka Kosowska, Polska",
    "working_hours": "Pon–Pt: 8:00–18:00, Sob: 9:00–14:00",
    "terms_content": _DEFAULT_TERMS,
    "privacy_content": _DEFAULT_PRIVACY,
    "faq_content": _DEFAULT_FAQ,
    "shipping_content": _DEFAULT_SHIPPING,
}

# Long-form content fields that get lazily backfilled onto a settings row that
# already existed before that column was added (e.g. the current dev/prod DB)
# — checked individually so adding a new one later doesn't need a new branch.
_CONTENT_FIELD_DEFAULTS = {
    "terms_content": _DEFAULT_TERMS,
    "privacy_content": _DEFAULT_PRIVACY,
    "faq_content": _DEFAULT_FAQ,
    "shipping_content": _DEFAULT_SHIPPING,
}


def _get_or_create(db: Session) -> SiteSettings:
    row = db.query(SiteSettings).first()
    if not row:
        row = SiteSettings(**_DEFAULTS)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    dirty = False
    for field, default in _CONTENT_FIELD_DEFAULTS.items():
        if not getattr(row, field, None):
            setattr(row, field, default)
            dirty = True
    if dirty:
        # Never overwrites real content — only fills in a field that's still empty.
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=SiteSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Public — powers the Contact page."""
    return _get_or_create(db)


@router.put("", response_model=SiteSettingsResponse)
def update_settings(
    payload: SiteSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    row = _get_or_create(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row
