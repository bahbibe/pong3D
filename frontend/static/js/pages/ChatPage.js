import { AbstractPage } from "./AbstarctPage.js";
import { ChatBox } from "../components/ChatBox.js";
import { Friends } from "../components/Friends.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const list = document.querySelector(".friends-list");
    const chatBox = document.querySelector(".chat-box");
    chatBox.innerHTML = `
      <div class="chat-box">
        <img class="loading" src="/static/img/loading.gif" alt="loading"/>
      </div>
    `;
    list.appendChild(new Friends());
    // chatBox.appendChild(this.chatBoxContainer());
  }
  // chatBoxContainer() {
  //   const chatBoxContainer = document.createElement("div");
  //   chatBoxContainer.innerHTML = `
  //   <div class="chat-box">
  //     <img class="loading" src="/static/img/loading.gif" alt="loading"/>
  //     <chat-box></chat-box>
  //   </div>
  //   `;
  //   return chatBoxContainer;
  // }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
