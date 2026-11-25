import { BASE_URL } from "./config.js";
import { toast } from "./toast.js";

/**
 * The one way to call the backend. Every call resolves (never throws) to
 *   {ok, status, data, message, errors}
 * matching the backend's {success, message, data, errors}. A network error
 * gives status 0. A request cancelled through `signal` gives {aborted: true}
 * (the page that asked is gone: show nothing).
 *
 * The body is sent as JSON, or as is when it is a FormData (file uploads).
 */

let onAuthProblem = () => {};

/**
 * Called with "unauthorized" (401: the session is gone) or "tfa" (the token
 * still waits for the 2FA code). The router installs it.
 */
export const setAuthHandler = (fn) => {
  onAuthProblem = fn;
};

const FALLBACK = "Something went wrong!. Please try again later";

export const request = async (method, path, { body, signal, auth = true } = {}) => {
  const init = { method, credentials: "include", signal, headers: {} };
  if (body instanceof FormData) {
    init.body = body;
  } else if (body !== undefined) {
    init.body = JSON.stringify(body);
    init.headers["Content-Type"] = "application/json";
  }

  let response;
  let payload;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
    payload = await response.json().catch(() => ({})); // a proxy error page is not JSON
  } catch (error) {
    if (error.name === "AbortError") return { ok: false, aborted: true, status: 0, errors: {} };
    return { ok: false, status: 0, message: "Network error, please try again.", errors: {} };
  }

  const tfaPending = payload?.data?.is_tfa_verified === false;
  const result = {
    ok: response.ok && payload.success !== false && !tfaPending,
    status: response.status,
    data: payload.data,
    message: payload.message || (response.ok ? "" : FALLBACK),
    errors: payload.errors || {},
  };
  // The handler redirects (login or 2FA page): no toast for these.
  if (auth && response.status === 401) result.authProblem = "unauthorized";
  else if (auth && tfaPending) result.authProblem = "tfa";
  if (result.authProblem) onAuthProblem(result.authProblem);
  return result;
};

const client = (signal) => ({
  get: (path, options = {}) => request("GET", path, { signal, ...options }),
  post: (path, body, options = {}) => request("POST", path, { body, signal, ...options }),
  put: (path, body, options = {}) => request("PUT", path, { body, signal, ...options }),
  del: (path, options = {}) => request("DELETE", path, { signal, ...options }),
});

export const api = {
  ...client(undefined),
  /** The same client, with every request cancelled when `signal` aborts. */
  withSignal: (signal) => client(signal),
};

/** Show a failed result in the toast. Returns result.ok. */
export const toastOnError = (result) => {
  if (!result.ok && !result.aborted && !result.authProblem) {
    toast.error(result.message || FALLBACK, result.errors);
  }
  return result.ok;
};
