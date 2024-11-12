import { AbstractPage } from "./AbstarctPage.js";
import API from "../API/API.js";

class TournamentDisplayPage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }
  connectedCallback() {
    const template = document.getElementById("tournament-display-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.API.getTournament(this.params.tournament_id).then((res) => {
        this.participants = res;
        console.log(this.participants);
        let player_number = 1 ;
        this.participants.data.forEach(participant => {
          let player_div = this.querySelector(`.player${player_number++}`)
          let image = document.createElement('img');
          image.src = new URL(participant.player.profile.avatar) ;
          player_div.appendChild(image) ;
        });
    });
  }
}

window.customElements.define("tournament-display-page", TournamentDisplayPage);
export { TournamentDisplayPage };
