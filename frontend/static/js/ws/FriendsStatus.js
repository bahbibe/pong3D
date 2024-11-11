export const FriendsStatus = () => {
  if (!window.socket) {
    const socket = new WebSocket('ws://localhost:8000/ws/status/');
    window.socket = socket;
  }

  socket.onopen = () => {
    console.log("connected to friends status websocket");
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("message received -> ", data);
    if (data.type === "user_status") {
      if (data.status === "offline") {
        window.online_users = data.online_users;
        const friend = document.querySelector(`#friend-${data.user_id}`);
        if (friend) {
          friend.querySelector(".user-status").classList.remove("online");
        }
      } else if (data.status === "online") {
        const online_users = data.online_users;
        window.online_users = online_users;
        for (const user of online_users) {
          const friend = document.querySelector(`#friend-${user}`);
          if (friend) {
            friend.querySelector(".user-status").classList.add("online");
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