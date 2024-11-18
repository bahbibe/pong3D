import { AbstractPage } from "./AbstarctPage.js";
import { Friends } from "../components/Friends.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    const rootElement = clone.firstElementChild;
    if (rootElement) {
      rootElement.className = "vh-100 d-flex flex-column";
    }
    this.appendChild(clone);
    this.friendslist = document.querySelector(".friends-list");
    this.friendslist.addEventListener("click", () => {
      this.friendslist.classList.add("toggle-list");
    }
    );
    this.friendslist.appendChild(new Friends());
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
