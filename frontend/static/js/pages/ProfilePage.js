import { AbstractPage } from "./AbstarctPage.js";

class ProfilePage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-profile");
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
    const toggler = this.querySelector(".toggler-btn");
    toggler.addEventListener("click", function () {
    document.querySelector("#sidebar").classList.toggle("collapsed");
    });

  }
}

window.customElements.define("user-profile", ProfilePage);
window.customElements.define("main-nav", mainNav);

export { ProfilePage }