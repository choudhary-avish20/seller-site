/**
 * Bug Condition Exploration Tests
 *
 * Task 1 — verified-user-login-json-error bugfix spec
 *
 * These tests MUST FAIL on unfixed code. Failure is the expected outcome and
 * confirms both bugs exist. Do NOT fix the source when they fail.
 *
 * Bug 1 (Requirements 1.2): req() calls res.json() with no .catch() on the
 *   success path, so any 2xx response with an empty/non-JSON body propagates
 *   an unhandled promise rejection instead of returning {}.
 *
 * Bug 2 (Requirements 1.3): The resend-verification click handler in
 *   login.html constructs its base URL as
 *   `localStorage.getItem('API_URL') || 'http://localhost:8000/api/v1'`
 *   rather than reading API.raw. In production (no localStorage override,
 *   non-localhost origin) the request is sent to the wrong host.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { JSDOM } from 'jsdom';

const __dirname = dirname(fileURLToPath(import.meta.url));
const APP_JS_PATH   = resolve(__dirname, '../js/app.js');
const LOGIN_HTML_PATH = resolve(__dirname, '../login.html');

// ---------------------------------------------------------------------------
// Helpers — build a fresh jsdom window that runs app.js so each test gets an
// isolated API instance without cross-contamination.
// ---------------------------------------------------------------------------

/**
 * Creates a clean jsdom window with app.js evaluated inside it.
 * @param {object} opts
 * @param {string}  [opts.origin]       - window.location.origin override
 * @param {object}  [opts.localStorage] - key/value pairs to pre-populate
 * @param {Function} [opts.fetchImpl]   - replacement for globalThis.fetch
 */
function buildWindow({ origin = 'http://localhost:8000', localStorage: lsData = {}, fetchImpl } = {}) {
  const dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: origin + '/login.html',
    runScripts: 'dangerously',
    resources: 'usable',
  });

  const { window } = dom;

  // Populate localStorage before app.js runs (it reads it at IIFE evaluation).
  for (const [k, v] of Object.entries(lsData)) {
    window.localStorage.setItem(k, v);
  }

  // Inject a stub __API_URL__ (not set) so app.js falls through to origin-based logic.
  window.__API_URL__ = undefined;

  // Wire fetch
  if (fetchImpl) {
    window.fetch = fetchImpl;
  }

  // Evaluate app.js in this window's context
  const appSource = readFileSync(APP_JS_PATH, 'utf-8');
  window.eval(appSource);

  return window;
}

// ---------------------------------------------------------------------------
// Bug 1 — req() JSON parse failure on 2xx response
// ---------------------------------------------------------------------------

describe('Bug 1 — req() must not throw when 2xx response body fails JSON parsing', () => {
  /**
   * Validates: Requirements 1.2
   *
   * EXPECTED ON UNFIXED CODE: rejects with SyntaxError
   *   ("Unexpected end of JSON input")
   * EXPECTED AFTER FIX: resolves to {}
   */
  it('returns {} instead of throwing when res.json() rejects on a 200 response', async () => {
    const jsonError = new SyntaxError('Unexpected end of JSON input');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: () => Promise.reject(jsonError),
      text: () => Promise.resolve(''),
    });

    const win = buildWindow({
      origin: 'https://wolkago.netlify.app',
      fetchImpl: mockFetch,
    });

    // API.getMe() delegates to req('/auth/me') — the simplest public method
    // that exercises the plain 2xx success path.
    const result = await win.API.getMe();

    // On FIXED code  → result should be {} (safe fallback)
    // On UNFIXED code → the promise rejects with SyntaxError (test fails here)
    expect(result).toEqual({});
  });

  it('returns {} instead of throwing when res.json() rejects with whitespace-only body (200)', async () => {
    const jsonError = new SyntaxError('Unexpected token   in JSON at position 0');

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: () => Promise.reject(jsonError),
      text: () => Promise.resolve('   '),
    });

    const win = buildWindow({
      origin: 'https://wolkago.netlify.app',
      fetchImpl: mockFetch,
    });

    const result = await win.API.getMe();

    // On FIXED code  → {}
    // On UNFIXED code → rejects with SyntaxError
    expect(result).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// Bug 2 — Resend handler uses hardcoded localhost instead of API.raw
// ---------------------------------------------------------------------------

/**
 * Builds a jsdom window from the actual login.html document so all DOM
 * elements (#resendLink, #f, etc.) exist before the inline scripts run.
 * Evaluates app.js first (so API/refreshUser/safeNextUrl are defined), then
 * evaluates the login.html inline handler script to wire up the click listener.
 *
 * @param {object} opts
 * @param {string}   [opts.origin]       - window.location.origin override
 * @param {object}   [opts.localStorage] - key/value pairs to pre-populate
 * @param {Function} [opts.fetchImpl]    - replacement for window.fetch
 */
function buildLoginWindow({ origin = 'http://localhost:8000', localStorage: lsData = {}, fetchImpl } = {}) {
  const loginHtml = readFileSync(LOGIN_HTML_PATH, 'utf-8');

  // Strip the external <script src="..."> tags AND the inline handler script
  // so JSDOM doesn't try to load/execute them during parsing (app.js isn't
  // available yet at parse time, so the inline script would throw).
  // We evaluate both manually in the correct order below.
  const strippedHtml = loginHtml
    .replace(/<script\s+src="[^"]*"[^>]*><\/script>/gi, '')
    .replace(/<script>([\s\S]*?)<\/script>\s*<\/body>/, '</body>');

  const dom = new JSDOM(strippedHtml, {
    url: origin + '/login.html',
    runScripts: 'dangerously',
    resources: 'usable',
  });

  const { window } = dom;

  // Populate localStorage before app.js runs (it reads it at IIFE evaluation).
  for (const [k, v] of Object.entries(lsData)) {
    window.localStorage.setItem(k, v);
  }

  // Stub __API_URL__ so app.js falls through to the origin-based logic.
  window.__API_URL__ = undefined;

  // Wire fetch before app.js runs so any DOMContentLoaded listeners it
  // registers also see the mock.
  if (fetchImpl) {
    window.fetch = fetchImpl;
  }

  // 1. Evaluate app.js — defines API, refreshUser, safeNextUrl, etc.
  const appSource = readFileSync(APP_JS_PATH, 'utf-8');
  window.eval(appSource);

  // 2. Evaluate the login.html inline handler script (the last <script> block
  //    in login.html) — wires up refreshUser() auto-redirect, the login form
  //    submit handler, and the resendLink click handler.
  const scriptMatch = loginHtml.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/);
  if (!scriptMatch) throw new Error('Could not extract login.html inline script');
  window.eval(scriptMatch[1]);

  return window;
}

describe('Bug 2 — resend-verification handler must use API.raw, not hardcoded localhost', () => {
  /**
   * Validates: Requirements 1.3
   *
   * Loads the actual login.html DOM and inline script in jsdom, then clicks
   * #resendLink to exercise the real handler (not a simulation).
   *
   * EXPECTED ON UNFIXED CODE: fetch is called with
   *   http://localhost:8000/api/v1/auth/resend-verification
   * EXPECTED AFTER FIX: fetch is called with a URL that starts with API.raw
   *   (i.e. https://wolkago.netlify.app/api/v1/auth/resend-verification)
   */
  it('sends resend request to API.raw base URL, not hardcoded localhost, in a production environment', async () => {
    const capturedFetchUrls = [];

    // Stub all fetch calls:
    //   /auth/me  → 401  so refreshUser() returns null and doesn't redirect.
    //   anything else → 200  so the resend handler completes without throwing.
    const mockFetch = vi.fn().mockImplementation((url, _opts) => {
      capturedFetchUrls.push(String(url));
      const isMe = String(url).includes('/auth/me');
      return Promise.resolve({
        ok: !isMe,
        status: isMe ? 401 : 200,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve(isMe ? { detail: 'Unauthorized' } : { detail: 'ok' }),
        text: () => Promise.resolve(isMe ? '' : 'ok'),
      });
    });

    // Production environment: non-localhost origin, no API_URL in localStorage.
    const productionOrigin = 'https://wolkago.netlify.app';
    const win = buildLoginWindow({
      origin: productionOrigin,
      localStorage: {
        // access_token must be present — the handler guards on it before calling fetch.
        access_token: 'fake-token-abc123',
        // Deliberately NO 'API_URL' key — mirrors the production situation.
      },
      fetchImpl: mockFetch,
    });

    // The expected correct base URL as app.js resolves it for this origin.
    const fixedBase = win.API.raw; // "https://wolkago.netlify.app/api/v1"

    // Allow the refreshUser() promise triggered by the inline script to settle
    // before we interact with the page.
    await new Promise(r => setTimeout(r, 0));

    // Clear any fetch calls made during page initialisation (refreshUser → /auth/me)
    // so we only inspect the resend call below.
    capturedFetchUrls.length = 0;

    // Click #resendLink to invoke the actual handler from login.html.
    const resendLink = win.document.getElementById('resendLink');
    expect(resendLink).not.toBeNull();
    resendLink.click();

    // Poll until the async handler fires fetch or we hit a 2 s safety timeout.
    const deadline = Date.now() + 2000;
    while (capturedFetchUrls.length === 0 && Date.now() < deadline) {
      await new Promise(r => setTimeout(r, 10));
    }

    expect(capturedFetchUrls.length).toBeGreaterThan(0);

    const actualUrl = capturedFetchUrls[0];

    // On UNFIXED code: actualUrl starts with 'http://localhost:8000' → FAILS.
    // On FIXED code:   actualUrl starts with fixedBase (production origin) → PASSES.
    expect(actualUrl).toMatch(new RegExp('^' + escapeRegExp(fixedBase)));
  });
});

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
