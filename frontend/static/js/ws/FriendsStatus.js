export const FriendsStatus = () => {
  if (!window.socket) {
    const socket = new WebSocket('ws://localhost:8000/ws/status/');
    window.socket = socket;
  }

  socket.onopen = () => {
    console.log("connected to friends status websocket");
  }

  socket.onmessage = (event) => {
    console.log("message received -> ", JSON.parse(event.data));
  }

  socket.onerror = (event) => {
    console.log("error", event);
  }

  socket.onclose = () => {
    window.socket = null;
    console.log("closed");
  }
}