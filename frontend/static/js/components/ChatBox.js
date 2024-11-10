import API from "../API/API.js";
import { Friends } from "./Friends.js";
import { WebSock } from "../ws/ws.js";
class ChatBox extends HTMLElement {
  constructor(uuid) {
    super();
    this.API = new API();
    this.ws = null;
    this.messages = [];
    this.uuid = "95b6631e-bde5-44d7-a42e-06986dc2a5ed";
  }
  connectedCallback() {
    this.API.getMessages(this.uuid).then((res) => {
      // this.messages =  dataBase;
      
      this.messages = res;

      this.render();
      // this.ws = new WebSock(this.uuid);
      // this.ws.connect();
      // this.ws.receive().then((data) => {
      //   const message = JSON.parse(data);
      //   this.messages.push(message);
      //   this.render();
      // });
    }
    );
  }

  async render() {
    this.appendChild(this.headerElement());
    try {
      this.messages.forEach((item) => {
        this.appendChild(this.createMessageElement(item));
      });
      if (this.messages.length === 0) {
        this.appendChild(document.createTextNode("No messages yet"));
      } 
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.appendChild(document.createTextNode("Error loading messages"));
    }
  }

  headerElement() {
    const headerElement = document.createElement("div");
    headerElement.classList.add("chat-header");
    headerElement.innerHTML = `
    <div class="avatar">
      <img src="https://via.placeholder.com/150" alt="avatar"/>
    </div>
    <div class="chat-info">
      <h5>Username</h5>
      <span>Active 3m ago</span>
    </div>
    `;
    return headerElement
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message-box");
    messageElement.innerHTML = `
    <div class="message-sender">
      <div class="message-info">
        <h5>${item.id}</h5>
      </div>
      <div class="message-item">
        <span>${item.content}</span>
        <!-- <span>${new Date(item.timestamp).toLocaleString()}</span> -->
        <span>${item.timestamp}</span>
      </div>
    </div>
       <div class="message-other">
      <div class="message-info">
        <h5>4ea85a6f-52aa-43c1-bd0f-ae853b70e43d</h5>
      </div>
      <div class="message-item">
        <span>lorem epsum</span>
        <!-- <span>${new Date(item.timestamp).toLocaleString()}</span> -->
        <span>${item.timestamp}</span>
      </div>
    </div>

    `;
    return messageElement;
  }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
