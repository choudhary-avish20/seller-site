function headerHTML(categories){
  // categories: array of tree nodes for pills
  const catPills = (categories||[]).slice(0,8).map(c=>`<a class="pill" href="categories.html">${c.name}</a>`).join('');
  // Actually pills should link to category page with slug param
  const pills2 = (categories||[]).slice(0,8).map(c=>`<a class="pill" href="category.html?slug=${c.slug}">${c.name}</a>`).join('');
  return `
  <div class="topbar"><div class="topbar__inner">
    <div style="display:flex;gap:16px;align-items:center">
      <span class="hide-sm" style="display:inline-flex;gap:6px;align-items:center"><span class="dot"></span><span data-i18n="b2bOnly">B2B only — zamówienia dla podmiotów gospodarczych</span></span>
      <a href="tel:+48579383945" class="hide-sm">+48 579 383 945</a>
      <span class="show-sm" data-i18n="b2bShort">Tylko B2B</span>
    </div>
    <div style="display:flex;gap:12px;align-items:center">
      <a href="categories.html" class="hide-md" data-i18n="categories">Kategorie</a>
      <a href="#" class="hide-md">Koszty wysyłki</a>
      <a href="#" class="hide-md">Regulamin</a>
      <span class="lang-toggle" style="display:inline-flex;border:1px solid #334155;border-radius:999px;overflow:hidden">
        <button data-lang="pl" style="padding:4px 10px;font-size:11px;background:${localStorage.getItem('lang')==='pl'?'#fff':'transparent'};color:${localStorage.getItem('lang')==='pl'?'#0f172a':'#cbd5e1'};border:0;cursor:pointer">PL</button>
        <button data-lang="en" style="padding:4px 10px;font-size:11px;background:${localStorage.getItem('lang')==='en'?'#fff':'transparent'};color:${localStorage.getItem('lang')==='en'?'#0f172a':'#cbd5e1'};border:0;cursor:pointer">EN</button>
      </span>
      <span id="auth-link"></span>
    </div>
  </div></div>
  <div class="header"><div class="header__main">
    <a href="index.html" class="logo"><div class="logo__mark">W</div><div class="hide-sm"><div class="logo__title">WHOLESALE</div><div class="logo__sub">CENTRUM • WÓLKA • B2B</div></div></a>
    <form id="searchForm" class="search"><input id="searchInput" data-i18n-ph="searchPh" placeholder="Szukaj — nazwa produktu, kategoria, SKU…" /><button type="submit" data-i18n="search">Szukaj</button></form>
    <div class="header__actions" style="display:flex;align-items:center;gap:8px">
      <a href="cart.html" class="cart-btn"><span class="cart-btn__meta"><span style="font-size:10px;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:.05em" data-i18n="cart">Koszyk</span><span style="font-size:14px;font-weight:600"><span data-cart-net>0.00 zł</span> <span style="font-weight:400;color:rgba(255,255,255,.7);font-size:11px" data-i18n="net">netto</span></span></span><span style="position:relative"><svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24"><path d="M6 6h15l-1.5 8H6z M6 6L5 2H2"/><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/></svg><span data-cart-badge class="cart-badge" style="display:none">0</span></span><span class="hide-lg" data-i18n="cart">Koszyk</span></a>
      <span id="header-auth"></span>
    </div>
  </div>
  <form id="searchFormMobile" class="search--mobile" style="padding:0 16px 12px;display:none"><input id="searchInputM" placeholder="Szukaj…" style="flex:1;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:999px;padding:12px 16px;font-size:14px"/><button type="submit" style="padding:0 20px;background:#0f172a;color:#fff;border:0;border-radius:999px">Szukaj</button></form>
  <div class="nav">
    <a href="index.html" data-i18n="new">Nowości</a>
    <a href="search.html" data-i18n="sale">Wyprzedaż</a>
    <a href="search.html" data-i18n="bestsellers">Bestsellery</a>
    <span style="width:1px;height:16px;background:#e2e8f0;margin:0 4px" class="hide-sm"></span>
    <a href="categories.html" class="active" data-i18n="allCats">Wszystkie kategorie</a>
    <a href="search.html" data-i18n="products">Produkty</a>
    <span style="margin-left:auto;font-size:11px;color:#64748b" class="hide-lg"><span style="width:8px;height:8px;background:#10b981;border-radius:50%;display:inline-block"></span> <span data-i18n="deliveryNote">Dostawa: do ustalenia • Podane ceny są</span> <b style="color:#0f172a" data-i18n="net">netto</b></span>
  </div>
  ${categories && categories.length ? `<div class="cat-pills">${pills2}<a href="categories.html" style="padding:6px 14px;font-size:12px;color:#4f46e5" data-i18n="all">Wszystkie →</a></div>` : ''}
  </div>
  `;
}
function injectHeader(categories){
  const mount = document.getElementById('site-header');
  if(!mount) return;
  mount.innerHTML = headerHTML(categories);
  // bind search
  const form = document.getElementById('searchForm');
  const formM = document.getElementById('searchFormMobile');
  const input = document.getElementById('searchInput');
  const inputM = document.getElementById('searchInputM');
  function go(e, inp){ e.preventDefault(); const q=(inp.value||'').trim(); location.href = q? `search.html?q=${encodeURIComponent(q)}` : 'search.html'; }
  if(form) form.addEventListener('submit', e=>go(e, input));
  if(formM) formM.addEventListener('submit', e=>go(e, inputM));
  // auth links - utility bar (small)
  const authLink = document.getElementById('auth-link');
  const token = localStorage.getItem('access_token');
  let isAuthed = !!token;
  let user = null;
  try{ user = JSON.parse(localStorage.getItem('user')||'null'); }catch{}
  if(authLink){
    if(isAuthed){
      authLink.innerHTML = user ? `<span style="color:#94a3b8;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block">${user.email}</span>` : `<a href="#" onclick="Auth.logout();return false;" style="color:#fff">Wyloguj</a>`;
    } else {
      authLink.innerHTML = `<a href="login.html" data-i18n="login">Zaloguj się</a>`;
    }
  }
  // header auth - prominent log in / log out (intended: log out → login.html to allow another account)
  const headerAuth = document.getElementById('header-auth');
  if(headerAuth){
    if(isAuthed){
      const email = user && user.email ? `<span style="display:none;color:#64748b;font-size:12px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" class="hide-lg">${user.email}</span>` : '';
      headerAuth.innerHTML = `${email}<button onclick="Auth.logout()" style="display:inline-flex;align-items:center;gap:6px;padding:8px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:999px;font-size:13px;font-weight:500;color:#334155;cursor:pointer"><svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24"><path d="M17 16l4-4-4-4 M21 12H9 M13 12a9 9 0 11-18 0 9 9 0 0118 0"/></svg><span data-i18n="logout">Wyloguj</span></button>`;
    } else {
      headerAuth.innerHTML = `<a href="login.html" style="display:inline-flex;align-items:center;gap:6px;padding:8px 14px;background:#0f172a;color:#fff;border-radius:999px;font-size:13px;font-weight:500;text-decoration:none"><svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24"><path d="M11 16l4-4-4-4 M15 12H3 M21 12a9 9 0 11-18 0 9 9 0 0118 0"/></svg><span data-i18n="login">Zaloguj się</span></a><a href="signup.html" style="display:none;padding:8px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:999px;font-size:13px;font-weight:500" class="hide-sm">Rejestracja</a>`;
    }
  }
  // lang toggle bind
  document.querySelectorAll('.lang-toggle [data-lang]').forEach(btn=>{
    btn.addEventListener('click', ()=>{ localStorage.setItem('lang', btn.dataset.lang); location.reload(); });
  });
  // update cart
  if(window.Cart) window.Cart.updateCartBadge();
  // re-apply i18n
  if(window.renderHeaderI18n) window.renderHeaderI18n();
}

function footerHTML(){
  return `<footer class="footer"><div class="footer__grid">
    <div><p style="font-weight:700;color:#0f172a">Wholesale Marketplace</p><p style="color:#64748b;margin-top:4px;font-size:13px">Wólka Kosowska inspired • modern B2B • pack-quantity cart • COD.</p></div>
    <div style="color:#475569"><p style="font-weight:600;color:#0f172a">Kontakt</p><p style="margin-top:4px">+48 579 383 945 • kontakt@wholesale.local</p><p style="font-size:12px;color:#94a3b8">Pn-Pt 8:00 - 17:00</p></div>
    <div style="color:#475569"><p style="font-weight:600;color:#0f172a">Informacje</p><div style="margin-top:4px;display:flex;gap:12px;font-size:12px"><a href="#">FAQ</a><a href="#">Koszty wysyłki</a><a href="#">Regulamin</a></div></div>
  </div><p style="text-align:center;font-size:11px;color:#94a3b8;margin-top:24px">Podane ceny są cenami netto • Brutto = netto + VAT • ${new Date().getFullYear()} Wholesale</p></footer>`;
}
function injectFooter(){
  const m=document.getElementById('site-footer');
  if(m) m.innerHTML=footerHTML();
}
window.injectHeader=injectHeader;
window.injectFooter=injectFooter;
