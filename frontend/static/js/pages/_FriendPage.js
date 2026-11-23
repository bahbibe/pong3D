import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class FriendPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("friend-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const friendId = this.getAttribute("params");
    console.log(JSON.parse(friendId));

  }
}


window.customElements.define("friend-page", FriendPage);


export { FriendPage }