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
    listProducts:(p={})=>{ const qs=new URLSearchParams(); if(p.search) qs.set('search',p.search); if(p.category_id) qs.set('category_id',p.category_id); if(p.limit) qs.set('limit',p.limit); if(p.page) qs.set('page',p.page); if(p.include_inactive) qs.set('include_inactive','true'); if(p.bestseller) qs.set('bestseller','true'); if(p.popular) qs.set('popular','true'); if(p.on_sale) qs.set('on_sale','true'); if(p.price_min!=null) qs.set('price_min',p.price_min); if(p.price_max!=null) qs.set('price_max',p.price_max); if(p.sort) qs.set('sort',p.sort); const s=qs.toString()? '?'+qs.toString():''; return req('/products'+s); },
    getProductBySlug:(s)=>req('/products/slug/'+s),
    getProductById:(id)=>req('/products/'+id),
    getCategoryBySlug:(s)=>req('/categories/by-slug/'+s),
    createOrder:(d)=>req('/orders',{method:'POST',body:JSON.stringify(d)}),
    listOrders:()=>req('/orders'),
    updateOrderStatus:(id,status)=>req('/orders/'+id+'/status',{method:'PATCH',body:JSON.stringify({status})}),
    hideOrder:(id)=>req('/orders/'+id+'/hide',{method:'PATCH'}),
    deleteOrder:(id)=>req('/orders/'+id,{method:'DELETE'}),
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
    // Coupons / discount codes
    validateCoupon:(code,orderNet)=>req('/coupons/validate',{method:'POST',body:JSON.stringify({code,order_net:orderNet})}),
    listCoupons:()=>req('/coupons'),
    createCoupon:(d)=>req('/coupons',{method:'POST',body:JSON.stringify(d)}),
    updateCoupon:(id,d)=>req('/coupons/'+id,{method:'PATCH',body:JSON.stringify(d)}),
    deleteCoupon:(id)=>req('/coupons/'+id,{method:'DELETE'}),
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

// Polish plural forms are three-way (1 / 2-4 except 12-14 / everything else),
// not the singular-vs-everything-else split English gets away with.
function plPluralPL(n, one, few, many){
  if(n === 1) return one;
  const lastDigit = n % 10, lastTwo = n % 100;
  if(lastDigit >= 2 && lastDigit <= 4 && !(lastTwo >= 12 && lastTwo <= 14)) return few;
  return many;
}
window.plPluralPL = plPluralPL;

// i18n
const I18N={
  pl:{b2b:'B2B only — zamówienia dla podmiotów gospodarczych',cat:'Kategorie',sale:'WYPRZEDAŻ',new:'Nowości',popular:'POPULAR',promo:'PROMOTIONS',searchPh:'Szukaj — nazwa produktu, kategoria...',search:'Szukaj',cart:'Koszyk',net:'net',gross:'gross',pack:'w paczce:',add:'Dodaj do koszyka',login:'Zaloguj się',logout:'Wyloguj',signup:'Rejestracja',contact:'Kontakt z nami',signinReminderTitle:'Zapisz swoje zamówienia i ulubione',signinReminderBody:'Zaloguj się, aby zachować listę życzeń i łatwiej zarządzać zamówieniami hurtowymi.',signinReminderCta:'Zaloguj się',signinReminderLater:'Może później'},
  en:{b2b:'B2B only — orders for business entities',cat:'Categories',sale:'SALE',new:'NEWS',popular:'POPULAR',promo:'PROMOTIONS',searchPh:'Search — product, category...',search:'Search',cart:'Cart',net:'net',gross:'gross',pack:'in a package:',add:'Add to cart',login:'Sign in',logout:'Sign out',signup:'Sign up',contact:'Contact us',signinReminderTitle:'Save your orders and favourites',signinReminderBody:'Sign in to keep your wishlist and manage your wholesale orders more easily.',signinReminderCta:'Sign in',signinReminderLater:'Maybe later'}
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
  },
  // Applied coupon — kept separate from the line-items array so clearing/editing
  // the cart doesn't silently drop it; checkout re-validates it server-side anyway.
  couponKey:'cart_coupon_v1',
  getCoupon(){ try{return JSON.parse(localStorage.getItem(this.couponKey)||'null')}catch{return null} },
  setCoupon(c){ localStorage.setItem(this.couponKey, JSON.stringify(c)); },
  clearCoupon(){ localStorage.removeItem(this.couponKey); },
  async applyCoupon(code){
    const {net}=this.totals();
    const res = await Api.validateCoupon(code, net);
    if(res.valid) this.setCoupon({code:res.code, discount_type:res.discount_type, discount_value:res.discount_value, min_order_net:res.min_order_net});
    else this.clearCoupon();
    return res;
  },
  // Recomputed live from the stored coupon rule against the CURRENT cart total, so a
  // percent coupon stays correct as quantities change (server re-validates at checkout).
  couponDiscount(){
    const c=this.getCoupon(); if(!c) return {amount:0, belowMin:false};
    const {net}=this.totals();
    if(c.min_order_net!=null && net < c.min_order_net) return {amount:0, belowMin:true, coupon:c};
    const amount = c.discount_type==='percent' ? +(net*c.discount_value/100).toFixed(2) : Math.min(c.discount_value, net);
    return {amount, belowMin:false, coupon:c};
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

// ── Shared product card ──────────────────────────────────────────────────
// One card component used by the homepage grid, search results, wishlist,
// and "you may also like" — so every catalogue surface looks and behaves
// identically instead of each page carrying its own hand-rolled markup.
// Cards register their product data in _productRegistry so cardChg()/
// cardAddToCart()/toggleWishlistCard() can look a product up by id no matter
// which section on the page rendered it.
window._productRegistry = window._productRegistry || new Map();

function renderProductCard(p){
  window._productRegistry.set(p.id, p);
  const out = p.stock_status === 'out_of_stock' || p.stock_quantity === 0;
  const img = p.images && p.images[0] ? Api.img(p.images[0]) : 'https://via.placeholder.com/400x400?text=No+image';
  const img2 = p.images && p.images[1] ? Api.img(p.images[1]) : null;
  const inc = p.pack_increment || 1;
  const showSale = p.is_on_sale && p.sale_price_net != null;
  const slugUrl = encodeURIComponent(p.slug);
  const packsLeft = Math.floor((p.stock_quantity || 0) / inc);
  const lowStock = packsLeft > 0 && packsLeft <= 2;

  let badge;
  if(showSale && p.discount_percent) badge = `<span class="pill pill-sale">-${p.discount_percent}%</span>`;
  else if(p.is_bestseller) badge = `<span class="pill">Bestseller</span>`;
  else if(p.is_popular) badge = `<span class="pill">Popularne</span>`;
  else badge = `<span class="pill">Nowość</span>`;

  const netGross = showSale
    ? `<div><s>${Number(p.price_net).toFixed(2)} PLN</s> <b style="color:var(--sale)">${Number(p.sale_price_net).toFixed(2)} PLN</b> netto</div>
       <div style="color:var(--text-secondary)">${Number(p.sale_price_gross).toFixed(2)} PLN brutto</div>`
    : `<div><b>${Number(p.price_net).toFixed(2)} PLN</b> netto</div>
       <div style="color:var(--text-secondary)">${Number(p.price_gross).toFixed(2)} PLN brutto</div>`;

  return `<div class="card">
    <div class="card-media">
      <a href="product.html?slug=${slugUrl}" class="card-img-wrap">
        <img class="img-a" src="${esc(img)}" alt="${esc(p.name)}" loading="lazy">
        ${img2 ? `<img class="img-b" src="${esc(img2)}" alt="" loading="lazy">` : ''}
      </a>
      <div class="badge-row">${badge}</div>
      <button class="wl-heart" data-id="${p.id}" onclick="toggleWishlistCard(this,'${p.id}')" aria-label="Dodaj do listy życzeń" title="Dodaj do listy życzeń">♡</button>
    </div>
    <h3><a href="product.html?slug=${slugUrl}">${esc(p.name)}</a></h3>
    ${p.review_count ? `<div style="font-size:11px;color:#f5a623">${'★'.repeat(Math.round(p.avg_rating))}${'☆'.repeat(5-Math.round(p.avg_rating))} <span style="color:var(--muted)">(${p.review_count})</span></div>` : ''}
    <div class="package-bar">Pack of ${p.pack_size} ${p.pack_size===1?'pair':'pcs'}</div>
    ${lowStock ? `<div class="stock-low">Only ${packsLeft} pack${packsLeft>1?'s':''} left</div>` : ''}
    <div class="price">${netGross}</div>
    <div class="qty">
      <button onclick="cardChg('${p.id}',-1)" aria-label="Zmniejsz ilość">−</button>
      <input id="qty-${p.id}" value="${inc}" data-inc="${inc}" inputmode="numeric">
      <button onclick="cardChg('${p.id}',1)" aria-label="Zwiększ ilość">+</button>
    </div>
    <button class="add" onclick="cardAddToCart(this,'${p.id}')" ${out?'disabled style="opacity:.5;cursor:not-allowed"':''}>${out?'Niedostępny':'Dodaj do koszyka'}</button>
  </div>`;
}

function cardChg(id, dir){
  const p = window._productRegistry.get(id);
  const inc = p ? (p.pack_increment || 1) : 1;
  const inp = document.getElementById('qty-'+id);
  if(!inp) return;
  let v = parseInt(inp.value || inc, 10) + dir*inc;
  if(v < inc) v = inc;
  v = Math.ceil(v/inc)*inc;
  inp.value = v;
}

// Cart.add() is a synchronous, local-only write — it cannot be "in
// progress" for any perceptible time, so there is no real async gap to
// show an "Adding…" state during. Showing the button's success state right
// after the (synchronous) call actually succeeds is the honest reading of
// "only show success after the operation confirms success" here.
function cardAddToCart(btn, id){
  const p = window._productRegistry.get(id);
  if(!p) return;
  const inc = p.pack_increment || 1;
  const inp = document.getElementById('qty-'+id);
  let qty = parseInt((inp && inp.value) || inc, 10);
  qty = Math.ceil(qty/inc)*inc;
  try{
    Cart.add(p, qty);
  }catch(e){
    showToast('Nie udało się dodać produktu do koszyka.');
    return;
  }
  flashAddedState(btn);
  showCartToast(p, qty);
}

// Briefly swaps a "Dodaj do koszyka" button to "✓ Dodano" and back —
// shared by the catalogue card button and the product-detail CTA.
function flashAddedState(btn){
  if(!btn) return;
  if(!btn.dataset.origLabel) btn.dataset.origLabel = btn.innerHTML;
  clearTimeout(btn._flashTimer);
  btn.disabled = true;
  btn.textContent = '✓ Dodano';
  btn._flashTimer = setTimeout(() => {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.origLabel;
  }, 1400);
}
window.flashAddedState = flashAddedState;

async function toggleWishlistCard(btn, id){
  const saved = await Wishlist.toggle(id);
  if(saved === null) return; // guest — redirected to login
  btn.textContent = saved ? '♥' : '♡';
  btn.classList.toggle('active', saved);
  showToast(saved ? 'Dodano do listy życzeń' : 'Usunięto z listy życzeń', saved ? { label: 'Zobacz listę', href: 'wishlist.html' } : null);
  renderWishlistMenu(getCachedUser());
}

function refreshWishlistHearts(){
  Wishlist.ids().then(ids=>{
    document.querySelectorAll('.wl-heart').forEach(btn=>{
      const savedItem = ids.has(btn.dataset.id);
      btn.textContent = savedItem ? '♥' : '♡';
      btn.classList.toggle('active', savedItem);
    });
  });
}

// Lightweight, dependency-free toast — used for wishlist/password feedback
// instead of blocking alert() dialogs. Optional `action` adds a single
// inline link (e.g. "View wishlist") without needing a second toast type.
let _toastTimer = null;
function showToast(msg, action){
  let el = document.getElementById('_toast');
  if(!el){
    el = document.createElement('div');
    el.id = '_toast';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    document.body.appendChild(el);
  }
  el.innerHTML = `<span>${esc(msg)}</span>` + (action ? `<a href="${esc(action.href)}" class="toast-action">${esc(action.label)}</a>` : '');
  el.classList.add('toast-visible');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('toast-visible'), 3200);
}
window.showToast = showToast;

// ── Add-to-cart confirmation toast ───────────────────────────────────────
// Richer than showToast() (product thumbnail, qty, two actions) since this
// is explicitly the most important post-add moment. Reuses the SAME
// #cart-count/#cart-net elements everywhere else (via Cart.add() already
// having updated them through updateCartUI()) — this toast carries no cart
// state of its own, just a link to the real cart page.
let _cartToastTimer = null;
function showCartToast(product, qty){
  let el = document.getElementById('_cartToast');
  if(!el){
    el = document.createElement('div');
    el.id = '_cartToast';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    document.body.appendChild(el);
  }
  const img = product.images && product.images[0] ? Api.img(product.images[0]) : '';
  el.innerHTML = `
    <div class="ct-toast-head">
      <span class="ct-toast-check" aria-hidden="true">✓</span>
      <span>Dodano do koszyka</span>
      <button class="ct-toast-close" type="button" aria-label="Zamknij" onclick="hideCartToast()">×</button>
    </div>
    <div class="ct-toast-body">
      ${img ? `<img src="${esc(img)}" alt="">` : ''}
      <div class="ct-toast-info">
        <div class="ct-toast-name">${esc(product.name)}</div>
        <div class="ct-toast-qty">${qty} szt.</div>
      </div>
    </div>
    <div class="ct-toast-actions">
      <button type="button" class="ct-toast-secondary" onclick="hideCartToast()">Kontynuuj zakupy</button>
      <a class="ct-toast-primary" href="cart.html">Przejdź do koszyka</a>
    </div>`;
  el.classList.add('visible');
  clearTimeout(_cartToastTimer);
  _cartToastTimer = setTimeout(hideCartToast, 5500);
}
function hideCartToast(){
  const el = document.getElementById('_cartToast');
  if(el) el.classList.remove('visible');
  clearTimeout(_cartToastTimer);
}
window.showCartToast = showCartToast;
window.hideCartToast = hideCartToast;
document.addEventListener('keydown', (e) => { if(e.key === 'Escape') hideCartToast(); });

window.renderProductCard = renderProductCard;
window.cardChg = cardChg;
window.cardAddToCart = cardAddToCart;
window.toggleWishlistCard = toggleWishlistCard;
window.refreshWishlistHearts = refreshWishlistHearts;

// ── Guest sign-in reminder ────────────────────────────────────────────────
// A once-per-session, dismissible nudge — never a login gate. Armed from
// renderAuthHeader() on every page load; sessionStorage (not localStorage)
// means it can show again in a future visit but never twice in one session,
// and logging in during the wait cancels it since the timer re-checks
// access_token right before displaying.
const SIGNIN_REMINDER_KEY = 'signin_reminder_shown_v1';
const SIGNIN_REMINDER_DELAY_MS = 60000;
const SIGNIN_REMINDER_SKIP_PAGES = ['login.html','signup.html','admin-login.html','admin-dashboard.html','register-seller.html','verify-email.html'];

function initSignInReminder(u){
  if(u) return; // signed in — never show
  if(SIGNIN_REMINDER_SKIP_PAGES.includes(location.pathname.split('/').pop())) return;
  let shown = false;
  try{ shown = sessionStorage.getItem(SIGNIN_REMINDER_KEY) === '1'; }catch{}
  if(shown) return;
  setTimeout(() => {
    if(localStorage.getItem('access_token')) return; // logged in during the wait
    try{ if(sessionStorage.getItem(SIGNIN_REMINDER_KEY) === '1') return; }catch{}
    showSignInReminder();
  }, SIGNIN_REMINDER_DELAY_MS);
}

function showSignInReminder(){
  try{ sessionStorage.setItem(SIGNIN_REMINDER_KEY, '1'); }catch{}
  const el = document.createElement('div');
  el.id = '_signinReminder';
  el.className = 'signin-reminder';
  el.setAttribute('role', 'complementary');
  el.setAttribute('aria-label', t('signinReminderTitle'));
  el.innerHTML = `
    <button type="button" class="signin-reminder-close" aria-label="Zamknij">×</button>
    <div class="signin-reminder-title">${esc(t('signinReminderTitle'))}</div>
    <div class="signin-reminder-body">${esc(t('signinReminderBody'))}</div>
    <div class="signin-reminder-actions">
      <a class="signin-reminder-cta" href="login.html">${esc(t('signinReminderCta'))}</a>
      <button type="button" class="signin-reminder-later">${esc(t('signinReminderLater'))}</button>
    </div>`;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('visible'));
  const dismiss = () => { el.classList.remove('visible'); setTimeout(() => el.remove(), 250); };
  el.querySelector('.signin-reminder-close').addEventListener('click', dismiss);
  el.querySelector('.signin-reminder-later').addEventListener('click', dismiss);
  document.addEventListener('keydown', function onEsc(e){
    if(e.key === 'Escape'){ dismiss(); document.removeEventListener('keydown', onEsc); }
  });
}
window.initSignInReminder = initSignInReminder;

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

// Cached copy of the last-fetched user (refreshUser() already persists this
// under 'user' on every call) — lets popovers re-render on a wishlist toggle
// etc. without an extra /auth/me round trip.
function getCachedUser(){
  try{ return JSON.parse(localStorage.getItem('user') || 'null'); }catch{ return null; }
}
window.getCachedUser = getCachedUser;

// Shared header auth state. Reads the one auth source of truth
// (refreshUser()/access_token) and drives every header element that depends
// on it: the "My orders" catnav link, the wishlist box visibility, the
// wishlist popover contents, and the account dropdown. No-ops safely on
// pages missing some of these elements (e.g. the admin dashboard, which
// manages its own header).
async function renderAuthHeader(){
  const myOrders = document.getElementById('myOrdersLink');
  const u = await refreshUser().catch(()=>null);
  if(myOrders) myOrders.style.display = (u && u.role==='buyer') ? '' : 'none';
  renderAccountMenu(u);
  renderWishlistMenu(u);
  initSignInReminder(u);
  return u;
}
document.addEventListener('DOMContentLoaded', renderAuthHeader);

// ── Shared dropdown wiring ──────────────────────────────────────────────
// Both the account menu and the wishlist popover are a `.acct-trigger`
// button next to a `.acct-panel` (the panel carries data-trigger="<button
// id>" so these generic, wire-once listeners can find and reset whichever
// trigger goes with whichever panel — no per-dropdown closures to leak or
// re-attach when a page re-renders its header (e.g. the PL/EN toggle calls
// renderAuthHeader() again).
function wireDropdown(triggerId, panelId){
  const trigger = document.getElementById(triggerId);
  const panel = document.getElementById(panelId);
  if(!trigger || !panel) return;
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    document.querySelectorAll('.acct-panel.open').forEach(p => {
      if(p !== panel){
        p.classList.remove('open');
        const t = document.getElementById(p.dataset.trigger);
        if(t) t.setAttribute('aria-expanded', 'false');
      }
    });
    const isOpen = panel.classList.toggle('open');
    trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  if(!window._dropdownGlobalListenersWired){
    window._dropdownGlobalListenersWired = true;
    document.addEventListener('click', (e) => {
      document.querySelectorAll('.acct-panel.open').forEach(p => {
        const t = document.getElementById(p.dataset.trigger);
        if(!p.contains(e.target) && e.target !== t){
          p.classList.remove('open');
          if(t) t.setAttribute('aria-expanded', 'false');
        }
      });
    });
    document.addEventListener('keydown', (e) => {
      if(e.key !== 'Escape') return;
      document.querySelectorAll('.acct-panel.open').forEach(p => {
        p.classList.remove('open');
        const t = document.getElementById(p.dataset.trigger);
        if(t) t.setAttribute('aria-expanded', 'false');
      });
    });
  }
}

// ── Account dropdown ────────────────────────────────────────────────────
// Injected into a `#accountMenuSlot` div already present in each page's
// header. Consolidates the features already scattered around the store
// (My Orders, Wishlist, Sign out) plus change-password — which the backend
// has always supported for any logged-in user (`POST /auth/change-password`)
// but no buyer-facing page ever exposed — into one panel, so a buyer has a
// single, obvious place to manage their account instead of hunting for a
// text link buried in the utility bar.
function renderAccountMenu(u){
  const slot = document.getElementById('accountMenuSlot');
  if(!slot) return;

  if(!u){
    slot.innerHTML = `<a href="login.html" class="cart" aria-label="Zaloguj się">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.5-7 8-7s8 3 8 7"/></svg>
      <span class="cart-copy">
        <span class="cart-label">Konto</span>
        <span class="cart-total">Zaloguj się</span>
      </span>
    </a>`;
    return;
  }

  const isBuyer = u.role === 'buyer';
  slot.innerHTML = `
    <div class="acct-menu">
      <button class="acct-trigger cart" id="acctTriggerBtn" type="button" aria-haspopup="true" aria-expanded="false">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.5-7 8-7s8 3 8 7"/></svg>
        <span class="cart-copy">
          <span class="cart-label">Konto</span>
          <span class="cart-total">${esc(u.full_name || u.email)}</span>
        </span>
        <svg class="acct-caret" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
      </button>
      <div class="acct-panel" id="acctPanel" data-trigger="acctTriggerBtn">
        <div class="acct-panel-head">
          <div class="acct-name">${esc(u.full_name || 'Twoje konto')}</div>
          <div class="acct-email">${esc(u.email)}</div>
        </div>
        <div class="acct-items">
          ${isBuyer ? `<a class="acct-item" href="orders.html">
            <svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a4 4 0 018 0v2"/></svg>
            Moje zamówienia
          </a>` : ''}
          ${isBuyer ? `<a class="acct-item" href="wishlist.html">
            <svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.35-9.5-8.5C1.2 9.5 2.5 6 6 6c2 0 3.4 1.3 4.5 2.8C11.6 7.3 13 6 15 6c3.5 0 4.8 3.5 3.5 6.5C16.5 16.65 12 21 12 21z"/></svg>
            Lista życzeń
          </a>` : ''}
          ${(u.role==='admin'||u.role==='seller') ? `<a class="acct-item" href="admin-dashboard.html">
            <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
            Panel admina
          </a>` : ''}
          <button class="acct-item" id="acctPwToggle" type="button">
            <svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>
            Zmień hasło
          </button>
          <div class="acct-divider"></div>
          <button class="acct-item danger" id="acctSignOutBtn" type="button">
            <svg viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4"/><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/></svg>
            Wyloguj się
          </button>
        </div>
        <div class="acct-pwform" id="acctPwForm">
          <div class="acct-pwform-inner">
            <input type="password" id="acctPwCurrent" placeholder="Obecne hasło" autocomplete="current-password">
            <input type="password" id="acctPwNew" placeholder="Nowe hasło (min. 8 znaków)" autocomplete="new-password">
            <button type="button" id="acctPwSubmit">Zapisz nowe hasło</button>
            <div class="acct-pw-msg" id="acctPwMsg"></div>
          </div>
        </div>
      </div>
    </div>`;

  wireDropdown('acctTriggerBtn', 'acctPanel');
  document.getElementById('acctSignOutBtn').addEventListener('click', () => doLogout());

  const pwForm = document.getElementById('acctPwForm');
  document.getElementById('acctPwToggle').addEventListener('click', () => {
    pwForm.classList.toggle('open');
  });
  document.getElementById('acctPwSubmit').addEventListener('click', async () => {
    const msg = document.getElementById('acctPwMsg');
    const current = document.getElementById('acctPwCurrent').value;
    const next = document.getElementById('acctPwNew').value;
    if(!current || !next){ msg.style.color = 'var(--sale)'; msg.textContent = 'Wypełnij oba pola.'; return; }
    if(next.length < 8){ msg.style.color = 'var(--sale)'; msg.textContent = 'Nowe hasło musi mieć min. 8 znaków.'; return; }
    try{
      await Api.changePassword({ current_password: current, new_password: next });
      msg.style.color = 'var(--success)';
      msg.textContent = 'Hasło zostało zmienione.';
      document.getElementById('acctPwCurrent').value = '';
      document.getElementById('acctPwNew').value = '';
      showToast('Hasło zostało zmienione');
    }catch(e){
      msg.style.color = 'var(--sale)';
      msg.textContent = e.message || 'Nie udało się zmienić hasła.';
    }
  });
}
window.renderAccountMenu = renderAccountMenu;

// ── Wishlist popover ────────────────────────────────────────────────────
// Injected into a `#wishlistMenuSlot` div next to the account menu slot.
// Reads the same Wishlist/Api.getWishlist() source of truth as the wishlist
// page itself — no separate count or item list is tracked here. Hidden
// entirely for guests/sellers/admins, same rule the old static wishlist box
// used.
async function renderWishlistMenu(u){
  const slot = document.getElementById('wishlistMenuSlot');
  if(!slot) return;
  if(!u || u.role !== 'buyer'){ slot.innerHTML = ''; return; }

  let items = [];
  try{ items = await Api.getWishlist(); }catch{}
  const n = items.length;
  const countText = n + ' ' + plPluralPL(n, 'produkt', 'produkty', 'produktów');
  const preview = items.slice(0, 3);

  const bodyHtml = n === 0
    ? `<div class="wish-empty">Twoja lista życzeń jest pusta.</div>`
    : `<div class="wish-items">${preview.map(it => {
        const p = it.product;
        const img = p.images && p.images[0] ? Api.img(p.images[0]) : '';
        return `<a class="wish-item" href="product.html?slug=${encodeURIComponent(p.slug)}">
          ${img ? `<img src="${esc(img)}" alt="">` : `<span class="wish-item-ph">📦</span>`}
          <span class="wish-item-name">${esc(p.name)}</span>
        </a>`;
      }).join('')}${n > preview.length ? `<div class="wish-more">+${n - preview.length} więcej</div>` : ''}</div>`;

  slot.innerHTML = `
    <div class="acct-menu">
      <button class="acct-trigger cart" id="wishTriggerBtn" type="button" aria-haspopup="true" aria-expanded="false">
        <svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.35-9.5-8.5C1.2 9.5 2.5 6 6 6c2 0 3.4 1.3 4.5 2.8C11.6 7.3 13 6 15 6c3.5 0 4.8 3.5 3.5 6.5C16.5 16.65 12 21 12 21z"/></svg>
        <span class="cart-copy">
          <span class="cart-label">Ulubione</span>
          <span class="cart-total" id="wishlistCountText">${countText}</span>
        </span>
      </button>
      <div class="acct-panel wish-panel" id="wishPanel" data-trigger="wishTriggerBtn">
        <div class="acct-panel-head"><div class="acct-name">Lista życzeń</div></div>
        ${bodyHtml}
        <div class="wish-panel-footer">
          <a href="wishlist.html" class="acct-item wish-view-all">Zobacz listę życzeń →</a>
        </div>
      </div>
    </div>`;

  wireDropdown('wishTriggerBtn', 'wishPanel');
}
window.renderWishlistMenu = renderWishlistMenu;
// Kept for backward compatibility with any inline call sites — refreshes
// the same wishlist popover rather than tracking a second count anywhere.
function updateWishlistBadge(){ renderWishlistMenu(getCachedUser()); }
window.updateWishlistBadge = updateWishlistBadge;

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

  // Trust strip: only genuinely true claims this store actually supports —
  // no invented "free returns" / "24h shipping" marketing fluff.
  el.innerHTML = `
    <div class="trust-strip"><div class="container">
      <div class="trust-item"><span class="ico">🏢</span><span>Sprzedaż wyłącznie B2B</span></div>
      <div class="trust-item"><span class="ico">🤝</span><span>Wsparcie dla firm</span></div>
      <div class="trust-item"><span class="ico">🚚</span><span>Dostawa własnym transportem</span></div>
      <div class="trust-item"><span class="ico">🔒</span><span>Bezpieczne zamówienia online</span></div>
    </div></div>
    <div class="footer-main"><div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <h4>WolkaGo</h4>
          <p>Hurtownia odzieży z Wólki Kosowskiej. Sprzedaż wyłącznie dla firm — płatność za pobraniem, dostawa własnym transportem.</p>
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
          <h4>Obsługa klienta</h4>
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
      </div>
    </div></div>`;

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

// PWA install support — static asset caching + offline shell only (see sw.js
// for why /api/* is deliberately excluded from caching).
if('serviceWorker' in navigator){
  window.addEventListener('load', ()=>{ navigator.serviceWorker.register('/sw.js').catch(()=>{}); });
}
