import { AbstractPage } from "./AbstarctPage.js";
import Profile from "./Profile.js";
import FriendsList from "./FriendsList.js";
import ChatBox from "./ChatBox.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.querySelector(".profile-container").appendChild(new Profile());
    this.querySelector(".friends-container").appendChild(new FriendsList());
    this.querySelector(".friends-container").addEventListener("click", (event) => {
      if (event.target.closest(".contact")) {
        this.renderChatBox(event);
      }
    });

  }
  async renderChatBox(event) {

    this.querySelector(".chat-container").appendChild(new ChatBox());
    

    // const chatBox = this.querySelector("#chat-box");
    // if (chatBox) {
    //   chatBox.parentNode.removeChild(chatBox);
    // }
    // const chatBoxElement = document.createElement("chat-box");
    // chatBoxElement.setAttribute("id", "chat-box");
    // chatBoxElement.setAttribute("friend", event.target.closest(".contact").id);
    // this.querySelector(".chat-container").appendChild(chatBoxElement);
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
