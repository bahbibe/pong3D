import { AbstractPage } from "./AbstarctPage.js";

class Home extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-home");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

class mainNav extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("main-nav");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("user-home", Home);

export { Home }