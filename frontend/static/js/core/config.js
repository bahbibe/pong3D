// The app is served by nginx on the same origin as the API and WebSockets.
// Relative URLs keep requests on that origin, so TLS is used and no CORS is
// needed.
export const BASE_URL = "";
export const WSS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
