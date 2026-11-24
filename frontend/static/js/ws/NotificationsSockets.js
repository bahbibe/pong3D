import { renderNotifications } from "../helpers.js";
import { BASE_URL } from "../router.js";
import { openReconnectingSocket } from "./reconnecting.js";

// Notifications sent while the socket was down are only in the database:
// reload the unread list after a reconnect.
const resync = async () => {
  try {
    const response = await fetch(`${BASE_URL}/api/auth/me/`, { credentials: "include" });
    const body = await response.json();
    if (body && body.success && body.data.notifications) {
      window.notifications = body.data.notifications;
      renderNotifications();
    }
  } catch (error) {
    console.error("Could not reload notifications:", error);
  }
};

export const Notifications = () => {
  if (window.notif_socket) return;
  window.notif_socket = openReconnectingSocket("/ws/notifications/", {
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      window.notifications = [...(window.notifications || []), data];
      renderNotifications();
    },
    onOpen: ({ reconnected }) => {
      if (reconnected) resync();
    },
    onStop: () => {
      window.notif_socket = null;
    },
  });
};
