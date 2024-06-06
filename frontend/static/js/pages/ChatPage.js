import { WebSockets } from "../ws/ws.js"

class ChatPage extends HTMLElement {

  constructor() {
    super()
    // get url from the window object
    const url = new URL(window.location.href);
    console.log('==============');
    console.log(url);
    console.log('==============');
    // this.ws = new WebSockets();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const send = this.querySelector("#chat-send");
    send.addEventListener("submit", this.handleSend.bind(this));
    // this.ws.connect();
  }
  async handleSend(e) {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:8000/api/friends/", {
        method: "GET",
        headers: {
          'content-type': 'application/json',
        },
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`API request failed with status: ${response.status}`);
      }
      const res = await response.json();
      const friend = res.data[0].friend;
      const message = this.querySelector("#chat-input").value.trim();
      if (!message) {
        return;
      }
      await this.ws.send({
        message: message,
        friend: friend.username,
      });
      let recivedMessage = await this.ws.receive();
      // append message to chat box
      const chatBox = this.querySelector("#chat-container");
      const messageDiv = document.createElement("div");
      messageDiv.textContent = recivedMessage;
      chatBox.appendChild(messageDiv);
      e.target.reset();
    } catch (error) {
      console.error("Error fetching profile data:", error);
    }

  }
}
window.customElements.define("chat-page", ChatPage);

export { ChatPage }