const DICT = {
  pl: {
    b2bOnly: "B2B only — zamówienia dla podmiotów gospodarczych",
    b2bShort: "Tylko B2B",
    categories: "Kategorie", shippingCosts:"Koszty wysyłki", terms:"Regulamin", login:"Zaloguj się",
    searchPh:"Szukaj — nazwa produktu, kategoria, SKU…", search:"Szukaj", cart:"Koszyk", net:"netto", netLong:"Podane ceny są netto",
    new:"Nowości", sale:"Wyprzedaż", bestsellers:"Bestsellery", allCats:"Wszystkie kategorie", products:"Produkty", deliveryNote:"Dostawa: do ustalenia • Podane ceny są",
    all:"Wszystkie →", bannerBusiness:"Informujemy, iż w naszej hurtowni mogą składać zamówienia tylko podmioty gospodarcze.", bannerSuffix:"— Wzorzec CentrumHurt, nowocześnie. Weryfikacja B2B przy zamówieniu.", becomeSeller:"Zostań sprzedawcą →",
    badge:"HURTOWNIA WÓLKA KOSOWSKA — ONLINE", hero1:"Hurt B2B.", hero2:"Packs, not pieces.", heroDesc:"Nowoczesne CentrumHurt: czysty katalog, ceny pack netto + brutto, boczny panel subkategorii — szybciej, lżej, mobile-first.",
    browseCats:"Przeglądaj kategorie", newBest:"Nowości / Bestsellery", trustShip:"Koszty wysyłki", trustShipD:"Do ustalenia • COD / faktura", trustB2B:"Tylko B2B", trustB2BD:"Weryfikacja NIP — jak CentrumHurt", trustNet:"Ceny netto", trustNetD:"Brutto = netto + VAT • pack pricing",
    featured:"Kategorie hurtowni", featuredD:"Taxonomia CentrumHurt — nowoczesne karty, podgląd subkategorii.", viewAll:"View all →", arrivals:"Nowości & Bestsellery", arrivalsD:"Najnowsze pack-produkty — jak CentrumHurt “Nowości”.",
    pack:"Pack", out:"Brak", available:"paczek dostępnych", add:"Dodaj", netPricesNote:"Ceny netto — dostawa do ustalenia",
    noImage:"Brak zdjęcia", noCat:"Bez kategorii", gross:"brutto",
  },
  en: {
    b2bOnly:"B2B only — orders for business entities", b2bShort:"B2B only",
    categories:"Categories", shippingCosts:"Shipping costs", terms:"Terms", login:"Sign in",
    searchPh:"Search — product, category, SKU…", search:"Search", cart:"Cart", net:"net", netLong:"Prices are net",
    new:"New", sale:"Sale", bestsellers:"Bestsellers", allCats:"All categories", products:"Products", deliveryNote:"Delivery: to be determined • Prices are",
    all:"All →", bannerBusiness:"Please note: only business entities can place orders in our wholesale store.", bannerSuffix:"— CentrumHurt pattern, modernized. B2B verified at checkout.", becomeSeller:"Become a seller →",
    badge:"WÓLKA KOSOWSKA WHOLESALE — ONLINE", hero1:"B2B wholesale.", hero2:"Packs, not pieces.", heroDesc:"Modernized CentrumHurt: clean catalog, pack pricing net + gross, subcategory sidebar like the reference — but faster, lighter, mobile-first.",
    browseCats:"Browse categories", newBest:"New / Bestsellers", trustShip:"Shipping costs", trustShipD:"To be determined • COD / invoice", trustB2B:"B2B only", trustB2BD:"VAT ID verified — like CentrumHurt", trustNet:"Net prices", trustNetD:"Gross = net + VAT • pack pricing",
    featured:"Wholesale categories", featuredD:"CentrumHurt taxonomy — modern cards, subcategory preview.", viewAll:"View all →", arrivals:"New & Bestsellers", arrivalsD:"Latest pack products — like CentrumHurt “New” section.",
    pack:"Pack", out:"Out of stock", available:"packs available", add:"Add", netPricesNote:"Net prices — delivery to be determined",
    noImage:"No image", noCat:"Uncategorized", gross:"gross",
  }
};
let lang = localStorage.getItem('lang') || (navigator.language.startsWith('pl')? 'pl' : (navigator.language.startsWith('en')?'en':'pl'));
if(!['pl','en'].includes(lang)) lang='pl';
function t(k){ return (DICT[lang] && DICT[lang][k]) || DICT['pl'][k] || k; }
function setLang(l){
  lang=l; localStorage.setItem('lang', l);
  document.documentElement.lang=l;
  renderHeaderI18n();
  // reload current page translations if needed
  if(window.onLangChange) window.onLangChange(l);
}
function renderHeaderI18n(){
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    const k=el.getAttribute('data-i18n');
    if(k) el.textContent=t(k);
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{
    const k=el.getAttribute('data-i18n-ph');
    if(k) el.placeholder=t(k);
  });
}
window.t=t; window.setLang=setLang; window.getLang=()=>lang; window.DICT=DICT;
document.addEventListener('DOMContentLoaded', ()=>{
  document.documentElement.lang=lang;
  // init toggles
  document.querySelectorAll('.lang-toggle [data-lang]').forEach(btn=>{
    btn.addEventListener('click', ()=>{ setLang(btn.dataset.lang); updateToggle(); });
  });
  updateToggle();
});
function updateToggle(){
  document.querySelectorAll('.lang-toggle [data-lang]').forEach(btn=>{
    if(btn.dataset.lang===lang) btn.classList.add('active');
    else btn.classList.remove('active');
  });
}
