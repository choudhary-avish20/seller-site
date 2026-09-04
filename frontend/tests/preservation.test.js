/**
 * Preservation Tests — verified-user-login-json-error bugfix spec
 *
 * Task 2 — These tests MUST PASS on UNFIXED code.
 * They encode the baseline behavior that the fix must not regress.
 *
 * Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { JSDOM } from 'jsdom';

const __dirname = dirname(fileURLToPath(import.meta.url));
const APP_JS_PATH = resolve(__dirname, '../js/app.js');

// ---------------------------------------------------------------------------
// Helpers — identical pattern to bug-condition-exploration.test.js
// ---------------------------------------------------------------------------

/**
 * Creates a clean jsdom window with app.js evaluated inside it.
 * @param {object} opts
 * @param {string}   [opts.origin]        - window.location.origin override
 * @param {object}   [opts.localStorage]  - key/value pairs to pre-populate
 * @param {Function} [opts.fetchImpl]     - replacement for globalThis.fetch
 */
function buildWindow({ origin = 'http://localhost:8000', localStorage: lsData = {}, fetchImpl } = {}) {
  const dom = new JSDOM('<!doctype html><html><body></body></html>', {
    url: origin + '/login.html',
    runScripts: 'dangerously',
    resources: 'usable',
  });

  const { window } = dom;

  for (const [k, v] of Object.entries(lsData)) {
    window.localStorage.setItem(k, v);
  }

  window.__API_URL__ = undefined;

  if (fetchImpl) {
    window.fetch = fetchImpl;
  }

  const appSource = readFileSync(APP_JS_PATH, 'utf-8');
  window.eval(appSource);

  return window;
}

/** Builds a minimal response mock that req() can consume. */
function mockResponse({ ok, status, statusText = '', contentType = 'application/json', jsonData, textData, jsonReject } = {}) {
  return {
    ok,
    status,
    statusText,
    headers: { get: (h) => h.toLowerCase() === 'content-type' ? contentType : null },
    json: jsonReject
      ? () => Promise.reject(jsonReject)
      : () => Promise.resolve(jsonData),
    text: () => Promise.resolve(textData ?? ''),
  };
}

// ---------------------------------------------------------------------------
// 1. Valid JSON 200 — returns parsed object (Requirement 3.1)
// ---------------------------------------------------------------------------

describe('Preservation 1 — valid JSON 200 returns the parsed object, not {}', () => {
  /**
   * Validates: Requirements 3.1
   *
   * The fix must NOT turn every 2xx response into {} — only those whose
   * .json() rejects. A successful .json() call must still return its value.
   */
  it('returns the parsed JSON object for a 200 response with a valid body', async () => {
    const body = { id: 'abc', role: 'buyer' };

    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({ ok: true, status: 200, jsonData: body })
      ),
    });

    const result = await win.API.getMe();

    expect(result).toEqual({ id: 'abc', role: 'buyer' });
    // Must NOT silently convert a real payload to {}
    expect(result).not.toEqual({});
  });

  it('returns a nested JSON object unchanged for a 200 response', async () => {
    const body = { products: [{ id: 1, name: 'Test' }], total: 1 };

    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({ ok: true, status: 200, jsonData: body })
      ),
    });

    const result = await win.API.listOrders();
    expect(result).toEqual(body);
  });
});

// ---------------------------------------------------------------------------
// 2. HTTP 204 — returns {} (Requirement 3.4)
// ---------------------------------------------------------------------------

describe('Preservation 2 — HTTP 204 returns {} via early-return branch', () => {
  /**
   * Validates: Requirements 3.4
   *
   * The early return at `if(res.status===204) return {};` must be unaffected.
   */
  it('returns {} for a 204 No Content response without touching the body', async () => {
    // .json and .text are defined but must NOT be called for a 204 —
    // if they were, jsdom would surface a warning. We assert the result is {}.
    const jsonSpy = vi.fn().mockRejectedValue(new Error('Should not call .json() on 204'));
    const textSpy = vi.fn().mockRejectedValue(new Error('Should not call .text() on 204'));

    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        statusText: 'No Content',
        headers: { get: () => null },
        json: jsonSpy,
        text: textSpy,
      }),
    });

    const result = await win.API.hideOrder('order-1');

    expect(result).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// 3. text/html response — returns the text string (Requirement 3.5)
// ---------------------------------------------------------------------------

describe('Preservation 3 — text/html response returns the text string', () => {
  /**
   * Validates: Requirements 3.5
   */
  it('returns the HTML string for a 200 text/html response', async () => {
    const htmlBody = '<html><body>hello</body></html>';

    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({ ok: true, status: 200, contentType: 'text/html; charset=utf-8', textData: htmlBody })
      ),
    });

    const result = await win.API.getMe();
    expect(result).toBe(htmlBody);
  });
});

// ---------------------------------------------------------------------------
// 4. 4xx error — throws with correct detail (Requirement 3.3)
// ---------------------------------------------------------------------------

describe('Preservation 4 — 4xx error throws with extracted detail', () => {
  /**
   * Validates: Requirements 3.3
   */
  it('throws an error with the detail message for a 401 Unauthorized response (no refresh token)', async () => {
    const win = buildWindow({
      // No access_token, no refresh_token — the 401 retry branch is NOT taken
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          jsonData: { detail: 'Incorrect email or password' },
        })
      ),
    });

    await expect(win.API.login('x@y.com', 'wrong')).rejects.toThrow('Incorrect email or password');
  });

  it('attaches .status to the thrown error for a 401 response', async () => {
    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          jsonData: { detail: 'Incorrect email or password' },
        })
      ),
    });

    let caught;
    try {
      await win.API.login('x@y.com', 'wrong');
    } catch (e) {
      caught = e;
    }

    expect(caught).toBeDefined();
    expect(caught.status).toBe(401);
    expect(caught.message).toBe('Incorrect email or password');
  });

  it('throws with detail for a 403 response', async () => {
    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue(
        mockResponse({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
          jsonData: { detail: 'Email not verified' },
        })
      ),
    });

    await expect(win.API.login('x@y.com', 'pass')).rejects.toThrow('Email not verified');
  });
});

// ---------------------------------------------------------------------------
// 5. 5xx error — statusText fallback when body isn't JSON (Requirement 3.3)
// ---------------------------------------------------------------------------

describe('Preservation 5 — 5xx error uses statusText fallback when body parse fails', () => {
  /**
   * Validates: Requirements 3.3
   *
   * The error path already has `.catch(()=>({detail:res.statusText}))` —
   * this must still work after the fix.
   */
  it('throws with statusText when the 500 response body is not JSON', async () => {
    const win = buildWindow({
      fetchImpl: vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: { get: () => 'text/plain' },
        json: () => Promise.reject(new SyntaxError('Unexpected token')),
        text: () => Promise.resolve('Internal Server Error'),
      }),
    });

    await expect(win.API.getMe()).rejects.toThrow('Internal Server Error');
  });
});

// ---------------------------------------------------------------------------
// 6. 401 retry with refresh token (Requirement 3.2)
// ---------------------------------------------------------------------------

describe('Preservation 6 — 401 with refresh token triggers transparent retry', () => {
  /**
   * Validates: Requirements 3.2
   *
   * req() should attempt a token refresh and replay the original request
   * when the first call returns 401 and a refresh_token is available.
   */
  it('retries the original request after a successful token refresh', async () => {
    const newAccessToken = 'new-access-token-xyz';
    const newRefreshToken = 'new-refresh-token-xyz';
    const userData = { id: 'user-1', role: 'buyer' };

    // Note: app.js registers a DOMContentLoaded listener that calls renderAuthHeader()
    // → refreshUser() → API.getMe() — this fires independently and also goes through
    // the 401→refresh→retry path because a refresh_token is present in localStorage.
    // We therefore cannot assert an exact fetch count; instead we verify the observable
    // behavior: req() returns the correct data AND the new tokens are persisted.
    //
    // Route by URL rather than call order to be robust against the background getMe().
    // Each call to /auth/me that carries the OLD token returns 401 once; the refresh
    // call always returns new tokens; any /auth/me with the new token returns userData.

    // Track which access tokens triggered a 401 so each is only rejected once.
    const rejectedTokens = new Set();

    const mockFetch = vi.fn().mockImplementation((url, opts) => {
      const authHeader = (opts && opts.headers && opts.headers['Authorization']) || '';
      const bearerToken = authHeader.replace('Bearer ', '');

      if (String(url).includes('/auth/refresh')) {
        // Refresh always succeeds and rotates the token
        return Promise.resolve(mockResponse({
          ok: true,
          status: 200,
          jsonData: { access_token: newAccessToken, refresh_token: newRefreshToken },
        }));
      }

      // First time we see the old token on a non-refresh request → 401
      if (bearerToken === 'old-access-token' && !rejectedTokens.has(bearerToken)) {
        rejectedTokens.add(bearerToken);
        return Promise.resolve(mockResponse({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          jsonData: { detail: 'Token expired' },
        }));
      }

      // Any request with the new (or already-rejected old) token → success
      return Promise.resolve(mockResponse({
        ok: true,
        status: 200,
        jsonData: userData,
      }));
    });

    const win = buildWindow({
      localStorage: {
        access_token: 'old-access-token',
        refresh_token: 'old-refresh-token',
      },
      fetchImpl: mockFetch,
    });

    const result = await win.API.getMe();

    // The explicit call must return the correct user data (proves retry succeeded)
    expect(result).toEqual(userData);
    // New tokens must be stored in localStorage after a successful refresh
    expect(win.localStorage.getItem('access_token')).toBe(newAccessToken);
    // At minimum: original + refresh + retry = 3 calls (background getMe may add more)
    expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(3);
    // The refresh endpoint must have been called at least once
    const refreshCalls = mockFetch.mock.calls.filter(([url]) => String(url).includes('/auth/refresh'));
    expect(refreshCalls.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// 7. Property-based: valid JSON bodies always return parsed object (Requirement 3.1)
// ---------------------------------------------------------------------------

describe('Preservation 7 — Property: valid JSON 2xx always returns the parsed object', () => {
  /**
   * Validates: Requirements 3.1
   *
   * For N random valid JSON objects as response bodies, req() must always
   * return the parsed object — never silently substitute {}.
   *
   * This is a manual property generator since fast-check is not in devDependencies.
   * It covers primitives, arrays, nested objects, empty objects, and special number values.
   */

  /** Generates a variety of valid JSON-serialisable values. */
  function* jsonCases() {
    // Primitives wrapped in objects (req() returns whatever res.json() gives)
    yield { id: 1 };
    yield { id: 'abc', role: 'buyer' };
    yield { a: true, b: false };
    yield { n: null };
    // Numeric edge cases
    yield { price: 0 };
    yield { price: -1 };
    yield { price: 1.23456789 };
    yield { price: Number.MAX_SAFE_INTEGER };
    // Nested structures
    yield { user: { id: 'u1', name: 'Alice' }, tokens: { access: 'tok' } };
    yield { items: [1, 2, 3], total: 3 };
    yield { items: [], total: 0 };
    // Unicode and special strings
    yield { name: 'Zażółć gęślą jaźń' };
    yield { name: '<script>alert(1)</script>' };
    yield { name: '"\'\\/\n\t\r' };
    // Large arrays
    yield { ids: Array.from({ length: 100 }, (_, i) => i) };
    // Empty object (valid JSON, must come back as {})
    yield {};
  }

  for (const expectedBody of jsonCases()) {
    it(`returns the parsed object for body: ${JSON.stringify(expectedBody).slice(0, 60)}`, async () => {
      const win = buildWindow({
        fetchImpl: vi.fn().mockResolvedValue(
          mockResponse({ ok: true, status: 200, jsonData: expectedBody })
        ),
      });

      const result = await win.API.getMe();

      // The result must deep-equal the original body.
      expect(result).toEqual(expectedBody);
    });
  }
});
