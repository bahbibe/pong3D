import { WSS_URL } from "../router.js";

class WebSock {
  constructor(uuid) {
    this.uuid = uuid;
    this.socket = new WebSocket(`${WSS_URL}/ws/chat/${uuid}/`);
  }

  async connect() {
    this.socket.onopen = () => {};
    this.socket.onerror = (error) => {
      console.error("error", error);
    };
    this.socket.onclose = (event) => {
      if (event.code === 4001) {
        alert("Unauthorized access. Please login.");
        window.location.href = "/login";
      }
    };
  }
  async send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error(
        "WebSocket is not open. ReadyState:",
        this.socket ? this.socket.readyState : "Socket is null",
      );
    }
  }
  async close() {
    if (this.socket) {
      this.socket.close();
    } else {
      console.error("WebSocket is not initialized.");
    }
  }
}

export { WebSock };
