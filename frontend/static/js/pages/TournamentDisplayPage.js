import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class TournamentDisplayPage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }
  connectedCallback() {
    console.log("connectedCallback");
    
    this.socket = new WebSocket('ws://localhost:8000/ws/tournament/' + this.params.tournament_id);
    const template = document.getElementById("tournament-display-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.socket.onmessage = e => {
      const res = JSON.parse(e.data)
      console.log(res);
      
      if (res.type == 'start')
      {
        const game = res.data.filter((elem) => elem.game.player1.username === user.username || elem.game.player2.username === user.username) ;
        if (game)
          console.log(game);
          
          // navigateTo(`/game/${game.id}`) ;
      }
      
      this.API.getTournamentGames(this.params.tournament_id).then((res) => {
        this.games = res;
        console.log(this.games);


        // if (player1 && player2 && (player1.username == user.username || player2.username == user.username) && (game.game.player1_score < 3 && game.game.player2_score < 3))
        //   navigateTo(`/game/${this.params.tournament_id}/${game.game.id}`)
        let game_it = 1;
        this.games.data.filter(game => game.t_round == 2).forEach(game => {
          const player1 = game.game.player1 ;
          const player2 = game.game.player2 ;
          const slots = this.querySelectorAll(`.game${game_it}`) ;
          const img_slot = slots[0].querySelector('.image') ;
          const img = document.createElement('img') ;
          img.src = player1.profile.avatar ;
          img_slot.replaceChildren(img) ;
          const name = slots[0].querySelector('.name') ;
          name.innerHTML = player1.username ;
          const score = slots[0].querySelector('.score') ;
          score.innerHTML = game.game.player1_score ;

          const img_slot2 = slots[1].querySelector('.image') ;
          const img2 = document.createElement('img') ;
          img2.src = player2.profile.avatar ;
          img_slot2.replaceChildren(img2) ;
          const name2 = slots[1].querySelector('.name') ;
          name2.innerHTML = player2.username ;
          const score2 = slots[1].querySelector('.score') ;
          score2.innerHTML = game.game.player2_score ;

        });

        // const lastgame = this.games.data.filter(game => game.t_round == 1)[0].game
        // if (lastgame.player1_score != lastgame.player2_score)
        // {
        //   const winner = lastgame.player1_score > lastgame.player2_score ? lastgame.player1 : lastgame.player2
        //   let winner_div = this.querySelector(`.winner`)
        //   winner_div.style = winner ? "border: #00FF00 3px solid" : "border: none" ;
        //   let image = document.createElement('img');
        //   image.src = new URL(winner.profile.avatar) ;
        //   winner_div.replaceChildren(image) ;
        // }
        
      });
    };
  }
  
  adoptedCallback() {
    console.log("Custom element moved to new page.");
  }

  attributeChangedCallback(name, oldValue, newValue) {
    console.log(`Attribute ${name} has changed.`);
  }
  disconnectedCallback() {
    this.socket.close() ;
    console.log("Custom element removed from page.");
  }
}

window.customElements.define("tournament-display-page", TournamentDisplayPage);
export { TournamentDisplayPage };
