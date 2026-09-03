// The site is deployed as a single Render service that serves this frontend
// and the backend API from the same origin (see backend/app/main.py's
// StaticFiles mount), so no backend URL needs to be injected here — app.js
// falls back to same-origin /api/v1 automatically.
// To point at a different backend for local testing:
//   localStorage.setItem('API_URL', 'https://your-backend.onrender.com/api/v1')
window.__API_URL__ = window.__API_URL__ || '';
