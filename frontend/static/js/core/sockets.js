import { WSS_URL } from "./config.js";

// Close codes sent by the server: the session is gone or not allowed.
// Reconnecting would only fail again, so stop.
const FINAL_CODES = new Set([4001, 4003]);
const MAX_DELAY_MS = 30000;

/**
 * Open a WebSocket on `path` and reopen it after a drop (server restart,
 * network change), waiting 1 s, 2 s, 4 s ... up to 30 s, with jitter.
 *
 * onMessage(event) gets every message. onOpen({ reconnected }) runs on each
 * open; `reconnected` is true after a drop, so the caller can resync state.
 * Returns a handle whose close() stops it for good (logout).
 */
export const openReconnectingSocket = (path, { onMessage, onOpen, onStop } = {}) => {
  let socket = null;
  let attempt = 0;
  let opened = false;
  let stopped = false;
  let timer = null;

  const stop = () => {
    if (stopped) return;
    stopped = true;
    clearTimeout(timer);
    if (onStop) onStop();
  };

  const connect = () => {
    socket = new WebSocket(`${WSS_URL}${path}`);
    socket.onopen = () => {
      const reconnected = opened;
      opened = true;
      attempt = 0;
      if (onOpen) onOpen({ reconnected });
    };
    socket.onmessage = (event) => {
      if (onMessage) onMessage(event);
    };
    socket.onclose = (event) => {
      if (stopped) return;
      if (FINAL_CODES.has(event.code)) {
        stop();
        return;
      }
      const base = Math.min(MAX_DELAY_MS, 1000 * 2 ** attempt);
      attempt += 1;
      timer = setTimeout(connect, base / 2 + Math.random() * (base / 2));
    };
  };

  connect();
  return {
    close() {
      stop();
      if (socket) socket.close();
    },
    get readyState() {
      return socket ? socket.readyState : WebSocket.CLOSED;
    },
  };
};
