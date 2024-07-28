import { AbstractPage } from "./AbstarctPage.js";

class RankingPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("ranking-page");
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

window.customElements.define("ranking-page", RankingPage);
// window.customElements.define("main-nav", mainNav);

export { RankingPage }