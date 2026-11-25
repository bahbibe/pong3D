// TEMPORARY bridge for the pages not moved to core/ yet; removed once the
// last one is (refactor Phase 3). The old window.* globals read and write
// the session and the stores, and the old DOM updates follow the stores.
import { session } from "./session.js";
import { notifications, presence } from "./store.js";

Object.defineProperties(window, {
  // Old pages read window.user, the settings page sets it, logout sets null.
  user: {
    configurable: true,
    get: () => session.user,
    set(value) {
      if (value) session.setUser(value);
      else session.clear();
    },
  },
  notifications: {
    configurable: true,
    get: () => notifications.get(),
    set(value) {
      notifications.set(value ?? []);
    },
  },
  online_users: {
    configurable: true,
    get: () => [...presence.get()],
  },
});

// Online dots of the profile friends list and the chat header.
const setOnline = (userId, online) => {
  const friend = document.querySelector(`#friend-${userId}`);
  if (friend) friend.querySelector(".user-status")?.classList.toggle("online", online);

  const chatFriendStatus = document.querySelector(`.stat-${userId}`);
  if (chatFriendStatus) {
    chatFriendStatus.classList.toggle("online", online);
    const label = chatFriendStatus.querySelector(".friend-status");
    if (label) label.textContent = online ? "Online" : "Offline";
  }
};

let shown = new Set();
presence.subscribe((online) => {
  for (const id of online) if (!shown.has(id)) setOnline(id, true);
  for (const id of shown) if (!online.has(id)) setOnline(id, false);
  shown = new Set(online);
});
