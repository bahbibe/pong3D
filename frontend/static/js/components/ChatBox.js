import { escapeHTML as esc } from "../escape.js";
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
    this.chatContainer.className = "chat-container no-scroll p-2 d-flex flex-column h-100";
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

  render() {
    try {
      this.messages.forEach((item) => {
        this.msgBox.appendChild(this.createMessageElement(item));
        this.msgBox.scrollTop = this.msgBox.scrollHeight;
      });
      if (this.messages.length === 0) this.msgBox.appendChild(this.emptyElement());
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.msgBox.appendChild(this.emptyElement("Error loading Messages"));
    }
  }

  emptyElement() {
    const emptyElement = document.createElement("div");
    emptyElement.id = "empty";
    emptyElement.className = "d-flex justify-content-center h-100 align-items-center";
    emptyElement.innerHTML = `
    <div class="d-flex flex-column gap-5 text-center">
      <span class="fs-2 fw-bold"> Hello !! </span>
    <span>  <i class="fa-solid fa-hand-sparkles fa-bounce fs-1"></i> </span>
    </div>`;
    return emptyElement;
  }

  inputElement() {
    const inputElement = document.createElement("form");
    inputElement.className = "input-group";
    inputElement.innerHTML = `
    <div class=" send w-100 d-flex justify-content-around align-items-center mt-2">
    <input type="text" class=" send-input me-0 h-100" placeholder="  Type a message" aria-label="Type a message" aria-describedby="button-addon2"/>
    <button class=" send-icon btn h-100" type="submit" id="button-addon2"><i class="fs-3 fa-solid fa-paper-plane"></i> </button>
    </div>`;
    inputElement.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = inputElement.querySelector("input");
      if (input.value.trim() === "") return;
      // The server sets the author from the session. Only send the text.
      const message = { content: input.value };
      input.value = "";
      this.ws.send(message);
    });
    return inputElement;
  }

  headerElement(friend) {
    const headerElement = document.createElement("div");
    headerElement.className = "msg-head mb-3 p-2 d-flex gap-2";
    const stat =
      window.online_users && window.online_users.includes(friend.id.toString())
        ? "Online"
        : "Offline";
    headerElement.innerHTML = `
    <div class="d-flex align-items-center">
      <img src="${esc(friend.profile.avatar)}" class=" d-block img-cover img-fluid rounded-circle h-100" alt="avatar"/>
    </div>
    <div class="chat-info d-flex flex-column flex-grow-1 justify-content-center">
    <a href="/friend/${esc(friend.profile.uuid)}">
      <span class="fs-5">${esc(friend.username)}</span>
      </a>
      <span class="stat opacity-75 stat-${esc(friend.id)} ${stat === "Online" ? "online" : ""}">
        <i class="fa-solid fa-circle"></i> <span class="friend-status">${stat}</span>
      </span>
    </div>
      <button class=" btn challenge"><span class="d-none d-md-block">Challenge</span> <i class="fa-solid fa-gamepad fs-2 d-md-none"></i> </button>
    `;
    headerElement.querySelector("button").addEventListener("click", () => {
      this.inviteToGame(friend);
    });
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
      <p>${esc(item.content)}</p>
    `;
    return messageElement;
  }
  async inviteToGame(friend) {
    await this.API.invite_friend(friend.id);
  }

  async receiveMessage() {
    try {
      const message = await this.ws.receive();
      if (!message) {
        return;
      }
      this.querySelector(".msg-box").appendChild(this.createMessageElement(JSON.parse(message)));
      this.msgBox.scrollTop = this.msgBox.scrollHeight;
      await this.receiveMessage();
    } catch (error) {
      console.error("Error receiving message:", error);
    }
  }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
