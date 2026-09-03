const API = (()=>{
  // Priority order:
  //  1. localStorage override (set manually in browser console for testing)
  //  2. window.__API_URL__ injected by Netlify build via config.js
  //  3. Same-origin /api/v1 (when backend serves the frontend directly, e.g. local dev or Render)
  //  4. localhost fallback for file:// development
  let base = localStorage.getItem('API_URL') || window.__API_URL__ || '';
  if(!base){
    if(location.protocol==='file:') base='http://localhost:8000/api/v1';
    else if(location.port==='8000' || location.port==='8002') base = location.origin + '/api/v1';
    else base = location.origin + '/api/v1';
  }
  const API_BASE = base.replace(/\/api\/v1\/?$/,'');
  const getT=()=>({a:localStorage.getItem('access_token'),r:localStorage.getItem('refresh_token')});
  const setT=(a,r)=>{localStorage.setItem('access_token',a);localStorage.setItem('refresh_token',r)};
  const clr=()=>{localStorage.removeItem('access_token');localStorage.removeItem('refresh_token')};
  async function refresh(){
    const {r}=getT(); if(!r) return false;
    try{const d=await (await fetch(base+'/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:r})})).json(); if(d.access_token){setT(d.access_token,d.refresh_token);return true} }catch{}
    clr(); return false;
  }
  async function req(path,opts={}){
    const h=Object.assign({'Content-Type':'application/json'},opts.headers||{});
    const {a}=getT(); if(a) h['Authorization']='Bearer '+a;
    let res=await fetch(base+path,Object.assign({},opts,{headers:h}));
    if(res.status===401 && getT().r){ if(await refresh()){ h['Authorization']='Bearer '+getT().a; res=await fetch(base+path,Object.assign({},opts,{headers:h}))}}
    if(!res.ok){ const e=await res.json().catch(()=>({detail:res.statusText})); const err=new Error(e.detail||'Error '+res.status); err.status=res.status; throw err}
    if(res.status===204) return {}; const ct=res.headers.get('content-type')||''; if(ct.includes('text/html')) return res.text(); return res.json();
  }
  function img(u){ if(!u) return ''; if(u.startsWith('http')) return u; if(u.startsWith('/')) return API_BASE+u; return u; }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  window.esc = esc;
  return {
    getConfig:()=>req('/auth/config'),
    login:(e,p)=>req('/auth/login',{method:'POST',body:JSON.stringify({email:e,password:p})}).then(d=>{setT(d.access_token,d.refresh_token);return d}),
    signup:(d)=>req('/auth/signup',{method:'POST',body:JSON.stringify(d)}),
    getMe:()=>req('/auth/me'),
    registerSeller:(d)=>req('/sellers/register',{method:'POST',body:JSON.stringify(d)}),
    getCategoryTree:(p={})=>req('/categories/tree'+(p.include_inactive?'?include_inactive=true':'')),
    listProducts:(p={})=>{ const qs=new URLSearchParams(); if(p.search) qs.set('search',p.search); if(p.category_id) qs.set('category_id',p.category_id); if(p.limit) qs.set('limit',p.limit); if(p.include_inactive) qs.set('include_inactive','true'); if(p.bestseller) qs.set('bestseller','true'); if(p.popular) qs.set('popular','true'); if(p.on_sale) qs.set('on_sale','true'); if(p.sort) qs.set('sort',p.sort); const s=qs.toString()? '?'+qs.toString():''; return req('/products'+s); },
    getProductBySlug:(s)=>req('/products/slug/'+s),
    getProductById:(id)=>req('/products/'+id),
    getCategoryBySlug:(s)=>req('/categories/by-slug/'+s),
    createOrder:(d)=>req('/orders',{method:'POST',body:JSON.stringify(d)}),
    listOrders:()=>req('/orders'),
    updateOrderStatus:(id,status)=>req('/orders/'+id+'/status',{method:'PATCH',body:JSON.stringify({status})}),
    uploadImage:(file)=>{
      const fd=new FormData(); fd.append('file',file);
      const h={}; const {a}=getT(); if(a) h['Authorization']='Bearer '+a;
      return fetch(base+'/uploads/image',{method:'POST',headers:h,body:fd}).then(async r=>{ if(!r.ok){const e=await r.json().catch(()=>({detail:'Upload failed'})); throw new Error(e.detail)} return r.json()});
    },
    // Seller profile
    getSellerProfile:()=>req('/sellers/me/profile'),
    createProduct:(d)=>req('/products',{method:'POST',body:JSON.stringify(d)}),
    updateProduct:(id,d)=>req('/products/'+id,{method:'PUT',body:JSON.stringify(d)}),
    deleteProduct:(id)=>req('/products/'+id,{method:'DELETE'}),
    toggleStock:(id,d)=>req('/products/'+id+'/stock',{method:'PATCH',body:JSON.stringify(d)}),
    archiveProduct:(id,force)=>req('/products/'+id+'/archive'+(force?'?force=true':''),{method:'PATCH'}),
    // Admin seller management
    getPendingSellers:()=>req('/sellers/pending'),
    approveSeller:(id,d)=>req('/sellers/'+id+'/approve',{method:'POST',body:JSON.stringify(d)}),
    // Admin buyer management
    getAllBuyers:()=>req('/auth/buyers'),
    getPendingBuyers:()=>req('/auth/buyers/pending'),
    approveBuyer:(id,d)=>req('/auth/buyers/'+id+'/approve',{method:'POST',body:JSON.stringify(d)}),
    // Wishlist
    getWishlist:()=>req('/wishlist'),
    addToWishlist:(productId)=>req('/wishlist/'+productId,{method:'POST'}),
    removeFromWishlist:(productId)=>req('/wishlist/'+productId,{method:'DELETE'}),
    // Saved delivery addresses
    getAddresses:()=>req('/addresses'),
    createAddress:(d)=>req('/addresses',{method:'POST',body:JSON.stringify(d)}),
    setDefaultAddress:(id)=>req('/addresses/'+id+'/default',{method:'PATCH'}),
    deleteAddress:(id)=>req('/addresses/'+id,{method:'DELETE'}),
    // Product reviews
    getReviews:(productId)=>req('/reviews/product/'+productId),
    submitReview:(productId,d)=>req('/reviews/product/'+productId,{method:'POST',body:JSON.stringify(d)}),
    deleteReview:(id)=>req('/reviews/'+id,{method:'DELETE'}),
    // Category CRUD (admin/seller only)
    createCategory:(d)=>req('/categories',{method:'POST',body:JSON.stringify(d)}),
    updateCategory:(id,d)=>req('/categories/'+id,{method:'PUT',body:JSON.stringify(d)}),
    deleteCategory:(id)=>req('/categories/'+id,{method:'DELETE'}),
    // Site-wide contact info (Contact page + admin settings)
    getSettings:()=>req('/settings'),
    updateSettings:(d)=>req('/settings',{method:'PUT',body:JSON.stringify(d)}),
    // Account management
    changePassword:(d)=>req('/auth/change-password',{method:'POST',body:JSON.stringify(d)}),
    img, base:API_BASE, raw:base
  };
})();
// expose both casings for legacy html (Api vs API)
const Api = API;
window.Api = API;
window.API = API;
window.getImageUrl = (u)=> (API.img ? API.img(u) : (u && u.startsWith('/') ? API.base+u : u));

// i18n
const I18N={
  pl:{b2b:'B2B only — zamówienia dla podmiotów gospodarczych',cat:'Kategorie',sale:'WYPRZEDAŻ',new:'Nowości',popular:'POPULAR',frequent:'MOST FREQUENTLY PURCHASED',promo:'PROMOTIONS',searchPh:'Szukaj — nazwa produktu, kategoria...',search:'Szukaj',cart:'Koszyk',net:'net',gross:'gross',pack:'w paczce:',add:'Add to cart',login:'Zaloguj się',logout:'Wyloguj',signup:'Rejestracja'},
  en:{b2b:'B2B only — orders for business entities',cat:'Categories',sale:'SALE',new:'NEWS',popular:'POPULAR',frequent:'MOST FREQUENTLY PURCHASED',promo:'PROMOTIONS',searchPh:'Search — product, category...',search:'Search',cart:'Cart',net:'net',gross:'gross',pack:'in a package:',add:'Add to cart',login:'Sign in',logout:'Sign out',signup:'Sign up'}
};
let lang=localStorage.getItem('lang')||(navigator.language.startsWith('pl')?'pl':'pl');
function t(k){return (I18N[lang]&&I18N[lang][k])||I18N.pl[k]||k}
function setLang(l){lang=l;localStorage.setItem('lang',l);applyLang(); updateCartUI(); renderAuthHeader();}
function applyLang(){ document.querySelectorAll('[data-i18n]').forEach(e=>{const k=e.getAttribute('data-i18n'); if(k&&I18N[lang][k]) e.textContent=I18N[lang][k]}); document.querySelectorAll('[data-i18n-ph]').forEach(e=>{const k=e.getAttribute('data-i18n-ph'); if(k&&I18N[lang][k]) e.placeholder=I18N[lang][k]}); }
document.addEventListener('DOMContentLoaded',()=>{ document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang))); applyLang(); });

// cart
const Cart={
  key:'cart_v1',
  get(){ try{return JSON.parse(localStorage.getItem(this.key)||'[]')}catch{return []}},
  save(v){ localStorage.setItem(this.key,JSON.stringify(v)); updateCartUI(); },
  add(p,qty=1, varId=null, label=null, priceNet=null){
    const inc=p.pack_increment||1;
    qty=Math.max(inc, Math.ceil(qty/inc)*inc);
    const items=this.get();
    const idx=items.findIndex(i=>i.product.id===p.id && (i.variantId||null)===(varId||null));
    if(idx>=0){ items[idx].packQuantity+=qty; const tot=items[idx].packQuantity; items[idx].packQuantity=Math.ceil(tot/inc)*inc; }
    else items.push({product:p, packQuantity:qty, variantId:varId, variantLabel:label, variantPriceNet:priceNet});
    this.save(items);
  },
  update(id,varId,qty){ let items=this.get(); const it=items.find(x=>x.product.id===id && (x.variantId||null)===(varId||null)); const inc=it? (it.product.pack_increment||1):1; qty=Math.max(inc, Math.ceil(qty/inc)*inc); items=items.map(x=> x.product.id===id && (x.variantId||null)===(varId||null)? {...x,packQuantity:qty}:x); this.save(items); },
  remove(id,varId){ this.save(this.get().filter(x=> !(x.product.id===id && (x.variantId||null)===(varId||null))))},
  clear(){ this.save([])},
  count(){return this.get().reduce((s,i)=>s+i.packQuantity,0)},
  // Single source of truth for a cart line's unit price — used by totals() here,
  // and by cart.html/checkout.html so all three never disagree on what a line costs.
  // variantPriceNet is reserved for a genuine SKU variant price override; when unset,
  // price is always recomputed live from the product's sale/tier data at current quantity.
  linePrice(it){
    const base=(it.product.is_on_sale && it.product.sale_price_net!=null)?it.product.sale_price_net:it.product.price_net;
    let n=it.variantPriceNet!=null?it.variantPriceNet:base;
    const tiers=it.product.price_tiers||[];
    if(!it.variantPriceNet && tiers.length){
      const s=[...tiers].sort((a,b)=>a.min_quantity-b.min_quantity);
      for(const tr of s){ const mx=tr.max_quantity??Infinity; if(it.packQuantity>=tr.min_quantity && it.packQuantity<=mx){ n=tr.price_net; break;}}
      if(it.packQuantity> s[s.length-1].min_quantity && !s.some(tr=> it.packQuantity>=tr.min_quantity && it.packQuantity<=(tr.max_quantity??Infinity))) n=s[s.length-1].price_net;
    }
    const vat=it.product.vat_rate||23;
    const g=+(n*(1+vat/100)).toFixed(2);
    return {net:n, gross:g};
  },
  totals(){
    let net=0,gross=0;
    this.get().forEach(it=>{
      const {net:n,gross:g}=this.linePrice(it);
      net+=n*it.packQuantity; gross+=g*it.packQuantity;
    });
    return {net,gross}
  }
};
function updateCartUI(){
  const c=Cart.count(); const t=Cart.totals();
  document.querySelectorAll('[data-cart-count]').forEach(e=>e.textContent=c);
  document.querySelectorAll('[data-cart-net]').forEach(e=>e.textContent=t.net.toFixed(2)+' zł');
}
document.addEventListener('DOMContentLoaded', updateCartUI);

// Wishlist — server-backed (requires login), with a client-side id cache so
// heart icons across the storefront can render filled/outline without a
// network round trip per card. toggle() sends the visitor to log in (and
// back) if they aren't authenticated, the same pattern checkout.html uses.
const Wishlist = {
  _ids: null,
  async ids(){
    if(this._ids) return this._ids;
    if(!localStorage.getItem('access_token')){ this._ids = new Set(); return this._ids; }
    try{ const items = await Api.getWishlist(); this._ids = new Set(items.map(i=>i.product_id)); }
    catch{ this._ids = new Set(); }
    return this._ids;
  },
  async has(productId){ return (await this.ids()).has(productId); },
  async toggle(productId){
    if(!localStorage.getItem('access_token')){
      const page = location.pathname.split('/').pop() || 'index.html';
      location.href = 'login.html?next=' + encodeURIComponent(page + location.search);
      return null;
    }
    const ids = await this.ids();
    if(ids.has(productId)){ await Api.removeFromWishlist(productId); ids.delete(productId); return false; }
    await Api.addToWishlist(productId); ids.add(productId); return true;
  },
};
window.Wishlist = Wishlist;

// Recently viewed products — per-browser, localStorage only, no backend
// involved. product.html calls track() on load; index.html calls ids() to
// render a strip. Newest first, deduped, capped at 8.
const RecentlyViewed = {
  key: 'recently_viewed_v1',
  track(productId){
    let ids = this.ids().filter(id => id !== productId);
    ids.unshift(productId);
    ids = ids.slice(0, 8);
    try{ localStorage.setItem(this.key, JSON.stringify(ids)); }catch{}
  },
  ids(){
    try{ return JSON.parse(localStorage.getItem(this.key) || '[]'); }catch{ return []; }
  },
};
window.RecentlyViewed = RecentlyViewed;

// auth helpers
async function doLogout(){
  localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user'); localStorage.removeItem('cart_v1');
  location.href='login.html';
}
async function refreshUser(){
  const tok=localStorage.getItem('access_token'); if(!tok) return null;
  try{ const u=await Api.getMe(); localStorage.setItem('user',JSON.stringify(u)); return u;}catch{ return null}
}

// Reads ?next=<page> from the current URL and returns it only if it's a
// plain same-site page filename — never an absolute/protocol-relative URL
// or a javascript: URI — so login.html can't be used as an open redirect.
function safeNextUrl(fallback){
  const next = new URLSearchParams(location.search).get('next');
  if(next && /^[a-zA-Z0-9_-]+\.html(\?[^\s]*)?$/.test(next)) return next;
  return fallback;
}
window.safeNextUrl = safeNextUrl;

// Shared header auth state. Every consumer-facing page includes a single
// <a id="top-login"> in its topbar; this is the one place that decides
// whether it reads "Sign in" or "email • Sign out", so pages can't drift
// out of sync with each other (or, on a page with two separate login
// indicators, with themselves) the way this used to be duplicated ad-hoc
// per page. No-ops on pages that don't opt in (e.g. the admin dashboard,
// which manages its own header).
async function renderAuthHeader(){
  const link = document.getElementById('top-login');
  const myOrders = document.getElementById('myOrdersLink');
  const wishlistLink = document.getElementById('wishlistNavLink');
  if(!link && !myOrders && !wishlistLink) return null;
  const topUser = document.getElementById('topUser');
  const u = await refreshUser().catch(()=>null);
  if(u){
    if(link){ link.textContent = u.email+' • '+t('logout'); link.href='#'; link.onclick=()=>{doLogout();return false}; }
    if(topUser) topUser.textContent = u.full_name || u.email;
    if(myOrders) myOrders.style.display = u.role==='buyer' ? '' : 'none';
    if(wishlistLink) wishlistLink.style.display = u.role==='buyer' ? '' : 'none';
  } else {
    if(link){ link.textContent = t('login'); link.href='login.html'; link.onclick=null; }
    if(topUser) topUser.textContent = '';
    if(myOrders) myOrders.style.display = 'none';
    if(wishlistLink) wishlistLink.style.display = 'none';
  }
  return u;
}
document.addEventListener('DOMContentLoaded', renderAuthHeader);

// Shared site footer + floating WhatsApp contact button. Every page includes
// a single <div id="site-footer"></div> placeholder before </body>; this is
// the one place that builds it, so footer links/content can't drift between
// pages the way the old per-page header auth checks used to. No-ops safely
// if the placeholder or the contact-info API call is missing.
async function renderFooter(){
  const el = document.getElementById('site-footer');
  if(!el) return;
  let s = {};
  try{ s = await Api.getSettings(); }catch{}

  el.innerHTML = `
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <h4>WolkaGo</h4>
          <p>Hurtownia odzieży z Wólki Kosowskiej. Sprzedaż wyłącznie dla firm — płatność za pobraniem, dostawa własnym transportem.</p>
          <div class="footer-badges">
            <span class="footer-badge">💵 Płatność za pobraniem</span>
            <span class="footer-badge">🚚 Własny transport</span>
            <span class="footer-badge">🏢 Tylko B2B</span>
          </div>
        </div>
        <div class="footer-col">
          <h4>Sklep</h4>
          <a href="index.html">Strona główna</a>
          <a href="index.html?filter=sale">Wyprzedaż</a>
          <a href="index.html?filter=bestseller">Bestsellery</a>
          <a href="wishlist.html">Lista życzeń</a>
          <a href="orders.html">Moje zamówienia</a>
        </div>
        <div class="footer-col">
          <h4>Informacje</h4>
          <a href="faq.html">FAQ</a>
          <a href="shipping.html">Koszty i czas dostawy</a>
          <a href="terms.html">Regulamin</a>
          <a href="privacy.html">Polityka prywatności</a>
          <a href="contact.html">Kontakt</a>
        </div>
        <div class="footer-col">
          <h4>Kontakt</h4>
          ${s.phone ? `<a href="tel:${esc(s.phone.replace(/[^\d+]/g,''))}">📞 ${esc(s.phone)}</a>` : ''}
          ${s.email ? `<a href="mailto:${esc(s.email)}">✉️ ${esc(s.email)}</a>` : ''}
          ${s.address ? `<p>📍 ${esc(s.address)}</p>` : ''}
          ${s.working_hours ? `<p>🕒 ${esc(s.working_hours)}</p>` : ''}
        </div>
      </div>
      <div class="footer-bottom">
        <span>© ${new Date().getFullYear()} WolkaGo. Wszystkie prawa zastrzeżone.</span>
        <span>Zbudowane na FastAPI + Python</span>
      </div>
    </div>`;

  if(s.whatsapp_number && !document.getElementById('waFloat')){
    const a = document.createElement('a');
    a.id = 'waFloat';
    a.className = 'wa-float';
    a.href = 'https://wa.me/' + s.whatsapp_number.replace(/[^\d]/g,'');
    a.target = '_blank';
    a.rel = 'noopener';
    a.title = 'Napisz do nas na WhatsApp';
    a.textContent = '💬';
    document.body.appendChild(a);
  }
}
document.addEventListener('DOMContentLoaded', renderFooter);

window.Cart = Cart;
window.doLogout = doLogout;
window.refreshUser = refreshUser;
window.renderAuthHeader = renderAuthHeader;
window.renderFooter = renderFooter;
window.updateCartUI = updateCartUI;
