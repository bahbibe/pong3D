import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class ScorePage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }

  connectedCallback() {
    const template = document.getElementById("score-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    if (this.params.game_id === 'bot')
    {
      const urlParams = new URLSearchParams(window.location.search);

      const player1 = this.querySelector('.player1') ;
      const player1_score = this.querySelector('#player1_score') ;
      player1_score.innerHTML = parseInt(urlParams.get('player1_score')) ;
      const player1_img = document.createElement('img') ;
      player1_img.src = user.profile.avatar ;
      player1.appendChild(player1_img) ;

      const player2 = this.querySelector('.player2') ;
      const player2_score = this.querySelector('#player2_score') ;
      player2_score.innerHTML = parseInt(urlParams.get('player2_score')) ;
      const player2_img = document.createElement('img') ;
      player2_img.src = '/static/asset/images/robots_welcome.svg' ;
      player2.appendChild(player2_img) ;

      const invite_to_play_button = this.querySelector("#invite_game") ;
      invite_to_play_button.onclick = (e) => {
        navigateTo('/play/bot') ;
      }
      return 
    }
    this.API.get_game(this.params.game_id).then(res => {
      if (res.game.player1)
      {
        const player1 = this.querySelector('.player1') ;
        const player1_score = this.querySelector('#player1_score') ;
        player1_score.innerHTML = res.game.player1_score ;
        const player1_img = document.createElement('img') ;
        player1_img.src = res.game.player1.profile.avatar ;
        player1.appendChild(player1_img) ;
      }
      if (res.game.player2)
      {
        const player2 = this.querySelector('.player2') ;
        const player2_score = this.querySelector('#player2_score') ;
        player2_score.innerHTML = res.game.player2_score ;
        const player2_img = document.createElement('img') ;
        player2_img.src = res.game.player2.profile.avatar ;
        player2.appendChild(player2_img) ;
      }
      const invite_to_play_button = this.querySelector("#invite_game") ;
      invite_to_play_button.onclick = (e) => {
        this.API.play_again(res.game.id) ;
      }
    }) ;
  }
}


window.customElements.define("score-page", ScorePage);
export { ScorePage };
