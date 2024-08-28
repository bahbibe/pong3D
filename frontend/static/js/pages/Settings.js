import { AbstractPage } from "./AbstarctPage.js";

class SettingsPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("settings-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}


window.customElements.define("settings-page", SettingsPage);

export { SettingsPage }