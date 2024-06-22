import { AbstractPage } from "./AbstarctPage.js";

class HomePage extends AbstractPage {
  constructor() {
    super();
    this.ws.connect()
  }

  connectedCallback() {
    const template = document.getElementById("home-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    // this.notify();
  }
}

window.customElements.define("home-page", HomePage);

export { HomePage }