import { AbstractPage } from "./AbstarctPage.js";
import Profile from "../components/Profile.js";
import Friends from "../components/Friends.js";
import ChatBox from "../components/ChatBox.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
    this.ws.connect();
    this.uuid = null;
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.querySelector(".profile-container").appendChild(new Profile());
    this.querySelector(".friends-container").appendChild(new Friends());
    // this.notify();
    this.querySelector("#friends-list").addEventListener("click", (event) => {
      if (event.target.closest(".contact")) {
        const chatBox = document.querySelector("chat-box");
        if (chatBox) {
          if (this.uuid === event.target.closest(".contact").id) {
            return;
          }
          chatBox.parentNode.removeChild(chatBox);
        }
        this.uuid = event.target.closest(".contact").id;
        const ChatBoxElm = new ChatBox(this.uuid);
        this.querySelector(".chat-container").appendChild(ChatBoxElm);
      }
    });
    this.querySelector(".chat-container").addEventListener("click", (event) => {
      if (event.target.id === "close-chat") {
        const chatBox = document.querySelector("chat-box");
        chatBox.parentNode.removeChild(chatBox);
      }
    });
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
