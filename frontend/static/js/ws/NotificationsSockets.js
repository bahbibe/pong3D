import { renderNotifications } from "../helpers.js";

export const Notifications = () => {
  if (!window.notif_socket) {
    const socket = new WebSocket('ws://localhost:8000/ws/notifications/');
    window.notif_socket = socket;
  }

  notif_socket.onopen = () => {
    // console.log("connected to notifications websocket");
  }

  notif_socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("notification received -> ", data);
    const notifications = window.notifications || [];
    notifications.push(data);
    // window.notifications = notifications;
    renderNotifications();
  }

  notif_socket.onerror = (event) => {
    console.log("error", event);
  }

  notif_socket.onclose = () => {
    window.notif_socket = null;
    console.log("closed");
  }
}