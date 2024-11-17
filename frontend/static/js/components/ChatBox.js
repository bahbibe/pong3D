import { API } from "../API/API.js";
import { WebSock } from "../ws/ws.js";
class ChatBox extends HTMLElement {
  constructor(friendship) {
    super();
    this.API = new API();
    this.ws = null;
    this.messages = [];
    this.friendship = friendship;
  }

  async getMessages() {
    this.messages = await this.API.getMessages(this.friendship.uuid);
    this.chatContainer = document.createElement("div");
    this.chatContainer.className =
      "chat-container no-scroll p-2 d-flex flex-column h-100";
    this.chatContainer.appendChild(this.headerElement(this.friendship.friend));
    this.msgBox = document.createElement("div");
    this.msgBox.className = "msg-box no-scroll p-2 flex-grow-1";
    this.chatContainer.appendChild(this.msgBox);
    this.chatContainer.appendChild(this.inputElement());
    this.appendChild(this.chatContainer);
    this.render();
    this.ws = new WebSock(this.friendship.uuid);
    this.ws.connect();
    this.receiveMessage();
  }
  connectedCallback() {
    this.getMessages();
    this.messages[this.messages.length - 1]
      ? (window.lastMsg = this.messages[this.messages.length - 1])
      : null;
  }

  disconnectedCallback() {
    this.ws ? this.ws.close() : null;
  }

  renderMessages() {
    try {
      this.messages.forEach((item) => {
        this.msgBox.appendChild(this.createMessageElement(item));
        this.msgBox.scrollTop = this.msgBox.scrollHeight;
      });
      if (this.messages.length === 0)
        this.msgBox.appendChild(this.emptyElement());
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.msgBox.appendChild(this.emptyElement("Error loading Messages"));
    }
  }

  emptyElement() {
    const emptyElement = document.createElement("div");
    emptyElement.className = "d-flex justify-content-center";
    emptyElement.innerHTML = `
    <span> No messages </span>
    `;
    return emptyElement;
  }

  inputElement() {
    const inputElement = document.createElement("form");
    inputElement.className = "input-group";
    inputElement.innerHTML = `
    <input type="text" class="form-control" placeholder="Type a message" aria-label="Type a message" aria-describedby="button-addon2"/>
    <button class="btn btn-outline-info" type="submit" id="button-addon2">Send</button>
    `;
    inputElement.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = inputElement.querySelector("input");
      if (input.value.trim() === "") return;
      const message = {
        author: window.user.username,
        content: input.value,
      };
      input.value = "";
      this.ws.send(message);
    });
    return inputElement;
  }

  headerElement(friend) {
    const headerElement = document.createElement("div");
    headerElement.className = "status mb-3 p-2 d-flex";
    headerElement.innerHTML = `
    <div class="col-2 ">
      <img src="${friend.profile.avatar}" class="img-fluid rounded-circle pe-1" width="60" alt="avatar"/>
    </div>
    <div class="chat-info col-10">
      <span>${friend.username}</span>
    </div>
    `;
    return headerElement;
  }

  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    item.author === window.user.username
      ? (messageElement.className = "msg-sent")
      : (messageElement.className = "msg-received");
    messageElement.innerHTML = `
      <p>${item.content}</p>
    `;
    return messageElement;
  }

  async receiveMessage() {
    try {
      const message = await this.ws.receive();
      if (!message) {
        return;
      }
      this.querySelector(".msg-container").appendChild(
        this.createMessageElement(JSON.parse(message))
      );
      this.msgBox.scrollTop = this.msgBox.scrollHeight;
      await this.receiveMessage();
    } catch (error) {
      console.error("Error receiving message:", error);
    }
  }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
