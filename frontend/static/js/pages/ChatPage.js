import { AbstractPage } from "./AbstarctPage.js";
import Profile from "../components/Profile.js";
import Friends from "../components/Friends.js";
import ChatBox from "../components/ChatBox.js";
import WebSock from "../ws/ws.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.querySelector(".profile-container").appendChild(new Profile());
    this.querySelector(".friends-container").appendChild(new Friends());
    this.querySelector("#friends-list").addEventListener("click", (event) => {
      if (event.target.closest(".contact")) {
        const chatBox = document.querySelector("chat-box");
        if (chatBox) {
          chatBox.parentNode.removeChild(chatBox);
        }
        const uuid = event.target.closest(".contact").id;
        const ChatBoxElm = new ChatBox(uuid);
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
