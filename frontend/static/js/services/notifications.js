import { api } from "../core/api.js";
import { openReconnectingSocket } from "../core/sockets.js";
import { notifications } from "../core/store.js";

// /ws/notifications/: new notifications are added to the store. Those sent
// while the socket was down are only in the database: the unread list is
// loaded again after a reconnect.
let handle = null;

const resync = async () => {
  const result = await api.get("/api/auth/me/", { auth: false });
  if (result.ok && result.data.notifications) notifications.set(result.data.notifications);
};

export const start = () => {
  if (handle) return;
  handle = openReconnectingSocket("/ws/notifications/", {
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      notifications.set((list) => [...list, data]);
    },
    onOpen: ({ reconnected }) => {
      if (reconnected) resync();
    },
    onStop: () => {
      handle = null;
    },
  });
};

export const stop = () => {
  handle?.close();
  handle = null;
};

/** Mark one notification as read (it leaves the list at once). */
export const markRead = async (uuid) => {
  notifications.set((list) => list.filter((n) => n.uuid !== uuid));
  await api.post(`/api/auth/notifications/mark_as_read/${encodeURIComponent(uuid)}/`);
};

/** Mark every notification as read. */
export const markAllRead = async () => {
  notifications.set([]);
  await api.post("/api/auth/notifications/mark_as_read/");
};
