import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";

class TournamentDisplayPage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }
  connectedCallback() {
    this.socket = new WebSocket(
      "ws://localhost:8000/ws/tournament/" + this.params.tournament_id
    );
    const template = document.getElementById("tournament-display-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.socket.onmessage = (e) => {
      console.log(e.data);

      this.API.getTournament(this.params.tournament_id).then((res) => {
        this.participants = res;
        console.log(this.participants);
        let player_number = 1;
        this.querySelectorAll(".player").forEach((div) => {
          div.innerHTML = "";
          div.style = "border: none";
        });
        this.participants.data.forEach((participant) => {
          let player_div = this.querySelector(`.player${player_number++}`);
          player_div.inn;
          let image = document.createElement("img");
          if (participant) player_div.style = "border: #00FF00 3px solid";
          else player_div.style = "border: none";
          image.src = new URL(participant.player.profile.avatar);
          player_div.replaceChildren(image);
        });
      });
    };
  }
}

window.customElements.define("tournament-display-page", TournamentDisplayPage);
export { TournamentDisplayPage };
