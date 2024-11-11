import { AbstractPage } from "./AbstarctPage.js";
import API from "../API/API.js";
import { navigateTo } from "../router.js";



class TournamentPage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }

  create_tournament = () =>
  {
    this.API.create_tournament().then((res) => {
      navigateTo(`/tournament/${res.data.uuid}`)
    })
  }

  connectedCallback() {
    const template = document.getElementById("tournament-page");
    const clone = template.content.cloneNode(true);
    let create_tournament_button = document.createElement('button') ;
    create_tournament_button.innerHTML = 'Create new tournament' ;
    create_tournament_button.onclick = (e) => { this.create_tournament();} ;
    clone.appendChild(create_tournament_button) ;
    this.appendChild(clone);
    this.list = document.createElement('ul') ;
    this.list.classList += "w-100 p-4"
    this.API.getTournaments().then((res) => {
        this.tournaments = res ;
        this.tournaments.data.forEach(element => {
          let elem = document.createElement('li') ;
          elem.classList = "d-flex alight-items-center justify-content-between py-1 px-4"
          let tourName = document.createElement('span')
          tourName.innerHTML = `${element.owner.username}'s Tournament` ;
          elem.appendChild(tourName) ;
          let join_button = document.createElement('button') ;
          join_button.innerHTML = element.is_participant == true ? 'Play' : 'Join'
          console.log(element);
          
          join_button.onclick = (e) => {join_tournament(element.uuid)} ;
          join_button.classList += "play px-3 py-1 fw-bold text-uppercase" ;
          elem.appendChild(join_button) ;
          this.list.appendChild(elem) ;
          
        }) ;
    });
    this.appendChild(this.list) ;
  }
}

async function join_tournament(tournament_id) {
  await fetch(`http://localhost:8000/game/join_tournament/${tournament_id}`,
    {
      method: "GET",
      headers: {
        "content-type": "application/json",
      },
      credentials: "include",
    })
  .then((res) => {
    navigateTo(`/tournament/${tournament_id}`) ;
    console.log(res);
    
  })
  .catch((err) =>
    {
      return ;
    }
  )
}

window.customElements.define("tournament-page", TournamentPage);
export { TournamentPage };
