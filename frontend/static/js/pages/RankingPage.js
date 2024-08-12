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


window.customElements.define("ranking-page", RankingPage);

export { RankingPage }