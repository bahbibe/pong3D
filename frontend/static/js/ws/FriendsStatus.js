import { WSS_URL } from "../router.js";

export const FriendsStatus = () => {
  if (!window.socket) {
    const socket = new WebSocket(`${WSS_URL}/ws/status/`);
    window.socket = socket;
  }

  socket.onopen = () => {
    // console.log("connected to friends status websocket");
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "user_status") {
      if (data.status === "offline") {
        window.online_users = data.online_users;
        const friend = document.querySelector(`#friend-${data.user_id}`);
        const chatFriendStatus = document.querySelector(`.stat-${data.user_id}`);

        if (friend)
          friend.querySelector(".user-status").classList.remove("online");

        if (chatFriendStatus) {
          chatFriendStatus.classList.remove("online");
          chatFriendStatus.querySelector(".friend-status").textContent = "Offline";
        }
      } else if (data.status === "online") {
        const online_users = data.online_users;
        window.online_users = online_users;

        for (const user of online_users) {
          const friend = document.querySelector(`#friend-${user}`);
          const chatFriendStatus = document.querySelector(`.stat-${data.user_id}`);

          if (friend)
            friend.querySelector(".user-status").classList.add("online");

          if (chatFriendStatus) {
            chatFriendStatus.classList.add("online");
            chatFriendStatus.querySelector(".friend-status").textContent = "Online";
          }
        }
      }
    }
  }

  socket.onerror = (event) => {
    console.log("error", event);
  }

  socket.onclose = () => {
    window.socket = null;
    console.log("closed");
  }
}