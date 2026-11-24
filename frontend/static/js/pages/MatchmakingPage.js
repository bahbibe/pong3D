import { AbstractPage } from "./AbstarctPage.js";
import { navigateTo, WSS_URL } from "../router.js";


class MatchmakingPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("matchmaking-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.find_match_button = this.querySelector("#find_match") ;
    this.message = this.querySelector("#loader-message") ;
    this.message.innerHTML = "Looking for a match..." ;
    this.loader = this.querySelector(".loader") ;
    this.addEventListener('click', this);
    this.socket = new WebSocket(`${WSS_URL}/ws/matchmaking`);
    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== "game_found") return;
      this.message.textContent = "Match Found!";
      this.loader.style.display = "none";
      this.redirectTimer = setTimeout(() => {
        navigateTo("/play/" + message.game_id);
      }, 2000);
    };
  }

  handleEvent(event) {
    this[`on${event.type}`](event)
  }

  onclick(e) {
    if (e.target.id === "find_match")
      console.log("finding match");

  }

  disconnectedCallback() {
    clearTimeout(this.redirectTimer);
    this.socket.close();
  }
}


window.customElements.define("matchmaking-page", MatchmakingPage);
export { MatchmakingPage };
