// Backend API URL. A single Render service serves both the API and this
// static frontend (see the "Consolidate deployment on a single Render
// service" commit), so app.js should always call its own origin —
// localhost:8000 locally, seller-site-2.onrender.com in production. Leave
// this empty so app.js's same-origin fallback handles both correctly.
// Only set this if the frontend is ever served from a different host than
// the backend again — e.g. for local dev pointed at a remote backend:
//   localStorage.setItem('API_URL', 'https://seller-site-2.onrender.com/api/v1')
window.__API_URL__ = '';
