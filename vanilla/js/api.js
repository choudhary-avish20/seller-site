let API_URL = (window.__API_URL) || localStorage.getItem('API_URL') || '';
if(!API_URL){
  if(location.protocol === 'file:'){
    API_URL = 'http://localhost:8000/api/v1';
  } else if(location.pathname.startsWith('/vanilla') || location.port === '8000' || location.port === '8002'){
    API_URL = location.origin + '/api/v1';
  } else {
    API_URL = 'http://localhost:8000/api/v1';
  }
}
const API_BASE = API_URL.replace(/\/api\/v1\/?$/, '');

function getTokens(){
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token')
  };
}
function setTokens(access, refresh){
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}
function clearTokens(){
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}
function getImageUrl(path){
  if(!path) return '';
  if(path.startsWith('http')) return path;
  if(path.startsWith('/')) return API_BASE + path;
  return path;
}

async function refreshToken(){
  const {refresh} = getTokens();
  if(!refresh) return false;
  try{
    const res = await fetch(`${API_URL}/auth/refresh`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({refresh_token:refresh})});
    if(!res.ok) throw new Error('refresh failed');
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  }catch{ clearTokens(); return false;}
}

async function apiFetch(path, opts={}){
  const headers = Object.assign({'Content-Type':'application/json'}, opts.headers||{});
  const {access} = getTokens();
  if(access) headers['Authorization'] = `Bearer ${access}`;
  let res = await fetch(`${API_URL}${path}`, Object.assign({}, opts, {headers}));
  if(res.status===401){
    const ok = await refreshToken();
    if(ok){
      const {access: a2} = getTokens();
      headers['Authorization'] = `Bearer ${a2}`;
      res = await fetch(`${API_URL}${path}`, Object.assign({}, opts, {headers}));
    }
  }
  if(!res.ok){
    const err = await res.json().catch(()=>({detail: `HTTP ${res.status}`}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if(res.status===204) return {};
  return res.json();
}

// helpers
const Api = {
  // auth
  signup(data){ return apiFetch('/auth/signup', {method:'POST', body:JSON.stringify(data)}); },
  login(email,password){ return apiFetch('/auth/login', {method:'POST', body:JSON.stringify({email,password})}); },
  getMe(){ return apiFetch('/auth/me'); },
  registerSeller(data){ return apiFetch('/sellers/register', {method:'POST', body:JSON.stringify(data)}); },
  getMySellerProfile(){ return apiFetch('/sellers/me/profile'); },
  // categories
  getCategoryTree(includeInactive=false){ return apiFetch(`/categories/tree?include_inactive=${includeInactive}`); },
  getCategoryBySlug(slug){ return apiFetch(`/categories/by-slug/${slug}`); },
  listProducts(params={}){
    const qs = new URLSearchParams();
    if(params.category_id) qs.set('category_id', params.category_id);
    if(params.search) qs.set('search', params.search);
    if(params.page) qs.set('page', params.page);
    if(params.limit) qs.set('limit', params.limit);
    const s = qs.toString()?`?${qs.toString()}`:'';
    return apiFetch(`/products${s}`);
  },
  getProductBySlug(slug){ return apiFetch(`/products/slug/${slug}`); },
  getProduct(id){ return apiFetch(`/products/${id}`); },
  listMyProducts(){ return apiFetch('/products/my'); },
  createProduct(data){ return apiFetch('/products', {method:'POST', body:JSON.stringify(data)}); },
  updateProduct(id,data){ return apiFetch(`/products/${id}`, {method:'PUT', body:JSON.stringify(data)}); },
  deleteProduct(id){ return apiFetch(`/products/${id}`, {method:'DELETE'}); },
  toggleStock(id,data){ return apiFetch(`/products/${id}/stock`, {method:'PATCH', body:JSON.stringify(data)}); },
  archiveProduct(id){ return apiFetch(`/products/${id}/archive`, {method:'PATCH'}); },
  uploadImage(file){
    const fd = new FormData(); fd.append('file', file);
    const headers = {};
    const {access} = getTokens();
    if(access) headers['Authorization'] = `Bearer ${access}`;
    return fetch(`${API_URL}/uploads/image`, {method:'POST', headers, body: fd}).then(async r=>{
      if(!r.ok){ const e=await r.json().catch(()=>({detail:'Upload failed'})); throw new Error(e.detail);}
      return r.json();
    });
  },
  listTestImages(){ return apiFetch('/uploads/test-images'); },
  // orders
  createOrder(data){ return apiFetch('/orders', {method:'POST', body:JSON.stringify(data)}); },
  listOrders(){ return apiFetch('/orders'); },
  getOrder(id){ return apiFetch(`/orders/${id}`); },
  // sellers admin
  getPendingSellers(){ return apiFetch('/sellers/pending'); },
  approveSeller(id,status,reason){ return apiFetch(`/sellers/${id}/approve`, {method:'POST', body:JSON.stringify({status, rejection_reason:reason})}); },
  // category requests
  createCategoryRequest(data){ return apiFetch('/category-requests', {method:'POST', body:JSON.stringify(data)}); },
  listCategoryRequests(params={}){
    const qs=new URLSearchParams();
    if(params.status) qs.set('status',params.status);
    if(params.mine) qs.set('mine','true');
    const s=qs.toString()?`?${qs.toString()}`:'';
    return apiFetch(`/category-requests${s}`);
  },
  decideCategoryRequest(id,action,reason){ return apiFetch(`/category-requests/${id}/decision`, {method:'POST', body:JSON.stringify({action, rejection_reason:reason})}); },
};

window.Api = Api;
window.getImageUrl = getImageUrl;
window.API_BASE = API_BASE;
