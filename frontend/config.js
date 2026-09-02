// This file is overwritten at Netlify build time with the real backend URL.
// Locally it is a no-op — app.js falls back to same-origin /api/v1.
// To override manually: localStorage.setItem('API_URL', 'https://your-backend.onrender.com/api/v1')
window.__API_URL__ = window.__API_URL__ || '';
