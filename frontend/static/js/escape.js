// Escape a value before putting it inside an HTML template string.
// Use it for every value that comes from the server or from another user
// (usernames, chat messages, avatars, ids). Prefer textContent when you
// build nodes by hand.
const HTML_ESCAPES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
  "`": "&#96;",
};

export const escapeHTML = (value) =>
  String(value ?? "").replace(/[&<>"'`]/g, (char) => HTML_ESCAPES[char]);
