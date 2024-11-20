
import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class JoinPage extends AbstractPage {
    constructor() {
    super();
    this.API = new API();
    }

connectedCallback() {
    const template = document.getElementById("join-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    }
}


window.customElements.define("join-page", JoinPage);
export { JoinPage };
