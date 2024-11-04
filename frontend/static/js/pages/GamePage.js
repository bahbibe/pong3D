import { AbstractPage } from "./AbstarctPage.js";

class GamePage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("game-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("game-page", GamePage);
export { GamePage };