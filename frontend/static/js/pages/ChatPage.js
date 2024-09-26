import { AbstractPage } from "./AbstarctPage.js";
import {Friends} from "../components/Friends.js";
import {ChatBox} from "../components/ChatBox.js";
// import Profile from "../components/Profile.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
    // this.ws.connect();
    this.uuid = null;
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
