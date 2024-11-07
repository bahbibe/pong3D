import { AbstractPage } from "./AbstarctPage.js";
import { navigateTo } from "../router.js";


class MatchmakingPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("matchmaking-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.find_match_button = this.querySelector("#find_match") ;
    this.addEventListener('click', this);
    this.socket = new WebSocket('ws://localhost:8000/ws/matchmaking');
    this.socket.onopen = (event) =>
    {
      console.log("connected");
    }
    this.socket.onclose = (event) =>
    {
      console.log("connection closed");
    }
    this.socket.onmessage = (event) =>
    {
      let message = JSON.parse(event.data) ;
      console.log(message);
      if (message['type'] === 'game_found')
        navigateTo('/game/' + message['game_id']) ;
      
    }
  }

  handleEvent(event) {
    this[`on${event.type}`](event)
  }

  onclick(e) {
    if (e.target.id === "find_match")
      console.log("finding match");

  }
}


window.customElements.define("matchmaking-page", MatchmakingPage);
export { MatchmakingPage };