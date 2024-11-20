
import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class TourPage extends AbstractPage {
    constructor() {
    super();
    this.API = new API();
    }

connectedCallback() {
    const template = document.getElementById("tour-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    }
}


window.customElements.define("tour-page", TourPage);
export { TourPage };
