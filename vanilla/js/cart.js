const CART_KEY='cart_v1';
function getCart(){ try{return JSON.parse(localStorage.getItem(CART_KEY)||'[]')}catch{return []}}
function saveCart(items){ localStorage.setItem(CART_KEY, JSON.stringify(items)); updateCartBadge(); }
function addToCart(product, qty=1, variantId=null, variantLabel=null, variantPriceNet=null){
  const items=getCart();
  const idx=items.findIndex(i=>i.product.id===product.id && (i.variantId||null)===(variantId||null));
  if(idx>=0) items[idx].packQuantity += qty;
  else items.push({product, packQuantity:qty, variantId, variantLabel, variantPriceNet});
  saveCart(items);
}
function updateQty(productId,variantId,qty){
  let items=getCart();
  if(qty<1) return removeFromCart(productId,variantId);
  items=items.map(i=> i.product.id===productId && (i.variantId||null)===(variantId||null) ? Object.assign({},i,{packQuantity:qty}) : i);
  saveCart(items);
}
function removeFromCart(productId,variantId){
  const items=getCart().filter(i=> !(i.product.id===productId && (i.variantId||null)===(variantId||null)));
  saveCart(items);
}
function clearCart(){ saveCart([]); }
function cartCount(){ return getCart().reduce((s,i)=>s+i.packQuantity,0); }
function cartTotals(){
  let net=0,gross=0;
  getCart().forEach(it=>{
    const vat = it.product.vat_rate||23;
    const n = it.variantPriceNet!=null ? it.variantPriceNet : it.product.price_net;
    const g = it.variantPriceNet!=null ? +(n*(1+vat/100)).toFixed(2) : it.product.price_gross;
    net+= n*it.packQuantity; gross+= g*it.packQuantity;
  });
  return {net, gross};
}
function updateCartBadge(){
  const count=cartCount();
  const {net}=cartTotals();
  document.querySelectorAll('[data-cart-count]').forEach(el=> el.textContent = count>0? String(count):'0');
  document.querySelectorAll('[data-cart-net]').forEach(el=> el.textContent = net.toFixed(2)+' zł');
  // toggle visibility
  document.querySelectorAll('[data-cart-badge]').forEach(el=>{
    el.textContent = count;
    el.style.display = count>0?'grid':'none';
  });
}
document.addEventListener('DOMContentLoaded', updateCartBadge);
window.Cart = { getCart, addToCart, updateQty, removeFromCart, clearCart, cartCount, cartTotals, saveCart, updateCartBadge };
