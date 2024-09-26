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
    list.appendChild(new Friends());
    const chatBox = document.querySelector(".chat-box");
    chatBox.appendChild(new ChatBox());
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
