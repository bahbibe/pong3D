import API from "../API/API.js";
import WebSock from "../ws/ws.js";

class ChatBox extends HTMLElement {
  constructor(uuid) {
    super();
    this.API = new API();
    this.uuid = uuid;
    this.WebSock = null;
  }
  connectedCallback() {
    const template = document.getElementById("chat");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
    this.WebSock = new WebSock(this.uuid);
    this.WebSock.connect();
    this.receiveMessage();
    this.querySelector("#chat-form").addEventListener("submit", (event) => {
      event.preventDefault();
      this.sendMessage(event);
    });
  }
  async receiveMessage() {
    try {
      const message = await this.WebSock.receive();
      if (!message) {
        return;
      }
      this.querySelector("#chat-messages").appendChild(
        this.createMessageElement(JSON.parse(message))
      );
      await this.receiveMessage();
    } catch (error) {
      console.error("Error receiving message:", error);
    }
  }

  disconnectedCallback() {
    if (this.WebSock) {
      this.WebSock.close();
    }
  }

  async render() {
    try {
      const closeChat = document.createElement("button");
      closeChat.setAttribute("id", "close-chat");
      closeChat.innerText = "Close X";
      this.querySelector("#chat-messages").appendChild(closeChat);
      const chat = await this.API.getMessages(this.uuid);
      chat.forEach((item) => {
        this.querySelector("#chat-messages").appendChild(
          this.createMessageElement(item)
        );
      });
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
    const message = event.target.querySelector("#chat-input").value;
    if (message) {
      try {
        await this.WebSock.send({
          content: message,
          timestamp: new Date(), //.toLocaltring(), if needed
          conversation: this.uuid,
        });
        event.target.reset();
      } catch (error) {
        console.error("Error sending message:", error);
      }
    }
  }
}

customElements.define("chat-box", ChatBox);

export default ChatBox;
