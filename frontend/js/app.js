const API = (()=>{
  let base = localStorage.getItem('API_URL') || '';
  if(!base){
    if(location.protocol==='file:') base='http://localhost:8000/api/v1';
    else if(location.port==='8000' || location.port==='8002') base = location.origin + '/api/v1';
    else base='http://localhost:8000/api/v1';
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
    if(!res.ok){ const e=await res.json().catch(()=>({detail:res.statusText})); throw new Error(e.detail||'Error '+res.status)}
    if(res.status===204) return {}; const ct=res.headers.get('content-type')||''; if(ct.includes('text/html')) return res.text(); return res.json();
  }
  function img(u){ if(!u) return ''; if(u.startsWith('http')) return u; if(u.startsWith('/')) return API_BASE+u; return u; }
  return {
    getConfig:()=>req('/auth/config'),
    login:(e,p)=>req('/auth/login',{method:'POST',body:JSON.stringify({email:e,password:p})}).then(d=>{setT(d.access_token,d.refresh_token);return d}),
    signup:(d)=>req('/auth/signup',{method:'POST',body:JSON.stringify(d)}),
    getMe:()=>req('/auth/me'),
    registerSeller:(d)=>req('/sellers/register',{method:'POST',body:JSON.stringify(d)}),
    getCategoryTree:(p={})=>req('/categories/tree'+(p.include_inactive?'?include_inactive=true':'')),
    listProducts:(p={})=>{ const qs=new URLSearchParams(); if(p.search) qs.set('search',p.search); if(p.category_id) qs.set('category_id',p.category_id); if(p.limit) qs.set('limit',p.limit); const s=qs.toString()? '?'+qs.toString():''; return req('/products'+s); },
    getProductBySlug:(s)=>req('/products/slug/'+s),
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
    archiveProduct:(id)=>req('/products/'+id+'/archive',{method:'PATCH'}),
    // Admin seller management
    getPendingSellers:()=>req('/sellers/pending'),
    approveSeller:(id,d)=>req('/sellers/'+id+'/approve',{method:'POST',body:JSON.stringify(d)}),
    // Category CRUD (admin/seller only)
    createCategory:(d)=>req('/categories',{method:'POST',body:JSON.stringify(d)}),
    updateCategory:(id,d)=>req('/categories/'+id,{method:'PUT',body:JSON.stringify(d)}),
    deleteCategory:(id)=>req('/categories/'+id,{method:'DELETE'}),
    // Site-wide contact info (Contact page + admin settings)
    getSettings:()=>req('/settings'),
    updateSettings:(d)=>req('/settings',{method:'PUT',body:JSON.stringify(d)}),
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
function setLang(l){lang=l;localStorage.setItem('lang',l);applyLang(); renderHeaderCart();}
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
  totals(){
    let net=0,gross=0;
    this.get().forEach(it=>{
      let n=it.variantPriceNet!=null?it.variantPriceNet:it.product.price_net;
      // tiered
      const tiers=it.product.price_tiers||[];
      if(!it.variantPriceNet && tiers.length){
        const s=[...tiers].sort((a,b)=>a.min_quantity-b.min_quantity);
        for(const tr of s){ const mx=tr.max_quantity??Infinity; if(it.packQuantity>=tr.min_quantity && it.packQuantity<=mx){ n=tr.price_net; break;}}
        if(it.packQuantity> s[s.length-1].min_quantity && !s.some(tr=> it.packQuantity>=tr.min_quantity && it.packQuantity<=(tr.max_quantity??Infinity))) n=s[s.length-1].price_net;
      }
      const vat=it.product.vat_rate||23;
      const g=+(n*(1+vat/100)).toFixed(2);
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

// auth helpers
async function doLogout(){
  localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user'); localStorage.removeItem('cart_v1');
  location.href='login.html';
}
async function refreshUser(){
  const tok=localStorage.getItem('access_token'); if(!tok) return null;
  try{ const u=await Api.getMe(); localStorage.setItem('user',JSON.stringify(u)); return u;}catch{ return null}
}
window.Cart = Cart;
window.doLogout = doLogout;
window.refreshUser = refreshUser;
window.updateCartUI = updateCartUI;
