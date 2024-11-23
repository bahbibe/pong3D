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
    
    this.socket = new WebSocket('wss://localhost/ws/tournament/' + this.params.tournament_id);
    const template = document.getElementById("tournament-display-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.socket.onmessage = e => {
      const res = JSON.parse(e.data)
      console.log(res);
      
      this.API.getTournamentGames(this.params.tournament_id).then((res) => {
        this.games = res;
        console.log(this.games);

        const get_winner = (game) => {
          if (game?.player1_score > game?.player2_score)
            return 0 ;
          else if (game?.player1_score < game?.player2_score)
            return 1 ;
          return undefined ;
        }

        let game_it = 1;
        this.games.data.filter(game => game.t_round == 2).sort((a, b) => a.game.id - b.game.id).forEach(game => {
          const slots = this.querySelectorAll(`.game${game_it++}`) ;

          const player1 = game.game.player1 ;
          if (player1)
            slots[0].classList.replace('winner-bottom', 'winner-top') ;
          const img_slot = slots[0].querySelector('.image') ;
          const img = document.createElement('img') ;
          img.src = player1?.profile?.avatar ?? "" ;
          img_slot.replaceChildren(img) ;
          const name = slots[0].querySelector('.name') ;
          name.innerHTML = player1?.username ?? "" ;
          const score = slots[0].querySelector('.score') ;
          score.innerHTML = game.game.player1_score ?? "0" ;

          const player2 = game.game.player2 ;
          if (player2)
            slots[1].classList.replace('winner-bottom', 'winner-top') ;
          const img_slot2 = slots[1].querySelector('.image') ;
          const img2 = document.createElement('img') ;
          img2.src = player2?.profile?.avatar ?? "" ;
          img_slot2.replaceChildren(img2) ;
          const name2 = slots[1].querySelector('.name') ;
          name2.innerHTML = player2?.username ?? "" ;
          const score2 = slots[1].querySelector('.score') ;
          score2.innerHTML = game.game.player2_score ?? "0" ;

          console.log("winner", get_winner(game.game));
          
          const winner = get_winner(game.game) ;
          if (winner == 0)
            slots[1]?.classList.replace('winner-top', 'winner-bottom')
          if (winner == 1)
            slots[0]?.classList.replace('winner-top', 'winner-bottom')

          if (player1 && player2 && (player1.username == user.username || player2.username == user.username) && (game.game.player1_score < 3 && game.game.player2_score < 3))
            navigateTo(`/game/${this.params.tournament_id}/${game.game.id}`) ;
        });


        this.games.data.filter(game => game.t_round == 1).forEach(game => {
          const slots = this.querySelectorAll(`.game${game_it++}`) ;

          const player1 = game.game.player1 ;
          if (player1)
            slots[0].classList.replace('winner-bottom', 'winner-top') ;
          const img_slot = slots[0].querySelector('.image') ;
          const img = document.createElement('img') ;
          img.src = player1?.profile?.avatar ?? "" ;
          img_slot.replaceChildren(img) ;
          const name = slots[0].querySelector('.name') ;
          name.innerHTML = player1?.username ?? "" ;
          const score = slots[0].querySelector('.score') ;
          score.innerHTML = game.game.player1_score ?? "0" ;

          const player2 = game.game.player2 ;
          if (player2)
            slots[1].classList.replace('winner-bottom', 'winner-top') ;
          const img_slot2 = slots[1].querySelector('.image') ;
          const img2 = document.createElement('img') ;
          img2.src = player2?.profile?.avatar ?? "" ;
          img_slot2.replaceChildren(img2) ;
          const name2 = slots[1].querySelector('.name') ;
          name2.innerHTML = player2?.username ?? "" ;
          const score2 = slots[1].querySelector('.score') ;
          score2.innerHTML = game.game.player2_score ?? "0" ;

          const winner = get_winner(game.game) ;
          if (winner == 0)
            slots[1]?.classList.replace('winner-top', 'winner-bottom')
          if (winner == 1)
            slots[0]?.classList.replace('winner-top', 'winner-bottom')

          if (player1 && player2 && (player1.username == user.username || player2.username == user.username) && (game.game.player1_score < 3 && game.game.player2_score < 3))
            navigateTo(`/game/${this.params.tournament_id}/${game.game.id}`) ;
        });

        const lastgame = this.games.data.filter(game => game.t_round == 1)[0].game
        if (lastgame.player1_score != lastgame.player2_score)
        {
          const slots = this.querySelector(`.winner`) ;

          slots.classList.replace('winner-bottom', 'winner-top') ;

          const winner = lastgame.player1_score > lastgame.player2_score ? lastgame.player1 : lastgame.player2
          const img_slot2 = slots.querySelector('.image') ;
          const img2 = document.createElement('img') ;
          img2.src = winner?.profile?.avatar ?? "" ;
          img_slot2.replaceChildren(img2) ;
          const name2 = slots.querySelector('.name') ;
          name2.innerHTML = winner?.username ?? "" ;
          const score2 = slots.querySelector('.score') ;
          score2.innerHTML = "" ;
        }
        
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
  }
}

window.customElements.define("tournament-display-page", TournamentDisplayPage);
export { TournamentDisplayPage };
