import API from "../API/API.js";
import { WebSock } from "../ws/ws.js";
class ChatBox extends HTMLElement {
  constructor(uuid) {
    super();
    this.API = new API();
    this.ws = null;
    this.messages = [];
    this.uuid = "95b6631e-bde5-44d7-a42e-06986dc2a5ed";
    this.friendItem = window.selectedFriend;
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
    });
  }
  render() {
    try {
      this.appendChild(this.headerElement());
      this.messages.forEach((item) => {
        this.appendChild(this.createMessageElement(item));
      });
      this.appendChild(this.inputElement());
      if (this.messages.length === 0) {
        this.appendChild(document.createTextNode("No messages yet"));
      }
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.appendChild(document.createTextNode("Error loading messages"));
    }
  }

  inputElement() {
    const inputElement = document.createElement("div");
    inputElement.className = "input-group send-msg";
    inputElement.innerHTML = `
    <input type="text" class="form-control" placeholder="Type a message" aria-label="Type a message" aria-describedby="button-addon2"/>
    <button class="btn btn-outline-secondary" type="button" id="button-addon2">Send</button>
    `;
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
    messageElement.innerHTML = `
    <div class="message-other">
      <h5>${this.friendItem.username}</h5>
    <div class="message-item">
      <span>lorem epsum lkhaslkhklaslk laksjkljakldjs </span>
    </div>
    </div>
    <div class="message-sender">
      <div class="message-info">
        <h5> Me </h5>
      </div>
      <div class="message-item">
        <span>ajshkjdhajshdjh alksjdkljaksj askljd</span>
      </div>
    </div>
    `;
    return messageElement;
  }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
