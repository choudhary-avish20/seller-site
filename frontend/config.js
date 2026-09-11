// Backend API URL. Points at the backend Render service so that:
//   - app.js API calls hit the correct host regardless of which service serves this file
//   - verify-email.html link hrefs resolve to the backend (not the static frontend host)
// For local dev, override in the browser console:
//   localStorage.setItem('API_URL', 'http://localhost:8000/api/v1')
window.__API_URL__ = 'https://seller-site-2.onrender.com/api/v1';
