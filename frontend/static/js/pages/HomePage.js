import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class HomePage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("home-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

class SearchBar extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-bar");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}class User extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-info");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("home-page", HomePage);
window.customElements.define("search-bar", SearchBar);
window.customElements.define("user-info", User);

export { HomePage }