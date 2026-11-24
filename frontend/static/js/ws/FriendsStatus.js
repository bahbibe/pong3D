import { openReconnectingSocket } from "./reconnecting.js";

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

const onMessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type !== "user_status") return;
  window.online_users = data.online_users;
  if (data.status === "offline") {
    setOnline(data.user_id, false);
  } else if (data.status === "online") {
    // The server sends the full list: refresh every friend shown.
    for (const userId of data.online_users) setOnline(userId, true);
  }
};

export const FriendsStatus = () => {
  if (window.socket) return;
  window.socket = openReconnectingSocket("/ws/status/", {
    onMessage,
    onStop: () => {
      window.socket = null;
    },
  });
};
