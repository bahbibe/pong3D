import { openReconnectingSocket } from "../core/sockets.js";
import { presence } from "../core/store.js";

// /ws/status/: every message carries the full list of online users.
let handle = null;

export const start = () => {
  if (handle) return;
  handle = openReconnectingSocket("/ws/status/", {
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      if (data.type !== "user_status") return;
      presence.set(new Set(data.online_users.map(String)));
    },
    onStop: () => {
      handle = null;
    },
  });
};

export const stop = () => {
  handle?.close();
  handle = null;
  presence.set(new Set());
};
