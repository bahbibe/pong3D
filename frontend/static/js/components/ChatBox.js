import API from "../API/API.js";
import { WebSock } from "../ws/ws.js";
class ChatBox extends HTMLElement {
  constructor() {
    super();
    this.API = new API();
    this.ws = null;
    this.messages = [];
    this.friendItem = window.selectedFriend;
  }
  connectedCallback() {
    const uuid = this.friendItem.profile.uuid;
    this.API.getMessages(uuid).then((res) => {
      this.messages = res;
      this.render();
      this.ws = new WebSock(uuid);
      this.ws.connect();
      this.ws.receive().then((data) => {
        const message = JSON.parse(data);
        this.messages.push(message);
        this.render();
      });
    });
  }
  disconnectedCallback() {
    this.ws.close();
  }
  render() {
    try {
      this.appendChild(this.headerElement());
      this.messages.forEach((item) => {
        this.appendChild(this.createMessageElement(item));
      });
      this.appendChild(this.inputElement());
      if (this.messages.length === 0) {
        this.appendChild(this.emptyElement());
      }
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.appendChild(document.createTextNode("Error loading messages"));
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
    const inputElement = document.createElement("div");
    inputElement.className = "input-group send-msg";
    inputElement.innerHTML = `
    <input type="text" class="form-control" placeholder="Type a message" aria-label="Type a message" aria-describedby="button-addon2"/>
    <button class="btn btn-outline-secondary" type="button" id="button-addon2">Send</button>
    `;
    inputElement.querySelector("button").addEventListener("click", () => {
      const input = inputElement.querySelector("input");
      const message = input.value;
      input.value = "";
      this.ws.send(message);
      this.messages.push({
        message: message,
        sender: "me",
      });
    }
    );
    return inputElement;
  }

  headerElement() {
    const headerElement = document.createElement("div");
    headerElement.className = "status mb-3 p-2 d-flex";
    headerElement.innerHTML = `
    <div class="col-2 ">
      <img src="${window.selectedFriend.profile.avatar}" class="img-fluid rounded-circle pe-1" width="60" alt="avatar"/>
    </div>
    <div class="chat-info col-10">
      <span>${this.friendItem.username}</span>
    </div>
    `;
    return headerElement;
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    messageElement.className = item.sender === "me" ? "message me" : "message";
    messageElement.innerHTML = `
    <div class="message-content">
      <p>${item.message}</p>
    </div>
    `;
    return messageElement;

}
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
