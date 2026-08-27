async function getCurrentUser(){
  const token = localStorage.getItem('access_token');
  if(!token) return null;
  try{
    const user = await Api.getMe();
    return user;
  }catch{ return null; }
}
function isLogged(){ return !!localStorage.getItem('access_token'); }
function logout(){
  clearTokens();
  localStorage.removeItem('user');
  try{ localStorage.removeItem('cart_v1'); localStorage.removeItem('cart'); }catch{}
  // allow immediate re-login / sign-up with another account
  // go to login page (not index) so user can choose
  if(location.pathname.endsWith('login.html') || location.pathname.endsWith('/login.html')){
    location.reload();
  } else {
    location.href='login.html';
  }
}
async function login(email,password){
  const data = await Api.login(email,password);
  setTokens(data.access_token, data.refresh_token);
  const user = await Api.getMe();
  localStorage.setItem('user', JSON.stringify(user));
  return user;
}
async function signup(email,password,full_name, role='buyer'){
  await Api.signup({email,password,full_name,role});
  return login(email,password);
}
async function registerSeller(payload){
  const res = await Api.registerSeller(payload);
  // auto login
  await login(payload.email, payload.password);
  return res;
}
function getUser(){ try{return JSON.parse(localStorage.getItem('user')||'null')}catch{return null} }

window.Auth = { getCurrentUser, isLogged, logout, login, signup, registerSeller, getUser };
