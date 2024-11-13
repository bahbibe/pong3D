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
    <div class="close-chat">
    <button class="btn btn-primary close-chat">X</button>
    </div>
    <div class="avatar">
      <img src="${window.selectedFriend.profile.avatar}" alt="avatar"/>
    </div>
    <div class="chat-info">
      <h5>${this.friendItem.username}</h5>
      <span>Active</span>
    </div>
    `;
    const btn = headerElement.querySelector(".close-chat");
    btn.addEventListener("click", () => {
      this.removeChatBox();
    }
    );
    return headerElement;
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    messageElement.innerHTML = `
    <div class="message-other">
     <h5>${this.friendItem.username}</h5>
   <div class="message-item">
     <span>lorem epsum lkhaslkhklaslk laksjkljakldjs </span>
     <!-- <span>${new Date(item.timestamp).toLocaleString()}</span> -->
   </div>
 </div>
    <div class="message-sender">
      <div class="message-info">
        <h5> Me </h5>
      </div>
      <div class="message-item">
        <span>ajshkjdhajshdjh alksjdkljaksj askljd</span>
        <!-- <span>${new Date(item.timestamp).toLocaleString()}</span> -->
      </div>
    </div>
    `;
    return messageElement;
  }

  removeChatBox() {
    this.remove();
    const list = document.querySelector(".friends-list");
    list.classList.remove("toggle-list");
  }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
