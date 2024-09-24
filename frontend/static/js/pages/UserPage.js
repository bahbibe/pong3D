import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class UserPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const friendId = this.getAttribute("params");
    console.log(JSON.parse(friendId));

  }
}


window.customElements.define("user-page", UserPage);


export { UserPage }