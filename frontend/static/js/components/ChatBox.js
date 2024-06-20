import API from "../API/API.js";
import WebSock from "../ws/ws.js";

class ChatBox extends HTMLElement {
  constructor(uuid) {
    super();
    this.API = new API();
    this.uuid = uuid;
  }
  connectedCallback() {
    const template = document.getElementById("chat");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
    this.querySelector("#chat-form").addEventListener("submit", (event) => {
      event.preventDefault();
      this.sendMessage(event);
    });
  }

  async render() {
    try {
      // this.WebSock = new WebSock(this.uuid);
      // await this.WebSock.connect();
      const chat = await this.API.getMessages(this.uuid);
      chat.forEach((item) => {
        this.querySelector("#chat-messages").appendChild(
          this.createMessageElement(item)
        );
      });
      const closeChat = document.createElement("button");
      closeChat.setAttribute("id", "close-chat");
      closeChat.innerText = "Close Chat";
      this.querySelector("#chat-messages").appendChild(closeChat);
      if (chat.length === 0) {
        const noMessages = document.createElement("p");
        noMessages.innerText = "No messages found";
        this.querySelector("#chat-messages").appendChild(noMessages);
      }
      
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.querySelector("#chat-list").innerHTML = "Error loading chat";
    }
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message");
    messageElement.innerHTML = `
      <li>
        <span>${item.content}</span>
        <span>${new Date(item.timestamp).toLocaleString()}</span>
      </li>
    `;
    return messageElement;
  }

  async sendMessage(event) {
    const message = event.target.querySelector("#message").value;
    if (message) {
      try {
        this.querySelector("#chat-messages").appendChild(
          this.createMessageElement({
            content: message,
            timestamp: new Date(),
          })
        );
        await this.WebSock.send({
          content: message,
          timestamp: new Date(),
          conversation: this.uuid,
        });
        event.target.querySelector("#message").value = "";
      } catch (error) {
        console.error("Error sending message:", error);
      }
    }
  }
}

customElements.define("chat-box", ChatBox);

export default ChatBox;
