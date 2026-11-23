
import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class JoinPage extends AbstractPage {
    constructor() {
    super();
    this.API = new API();
    }

    connectedCallback() {
        const template = document.getElementById("join-page");
        const clone = template.content.cloneNode(true);
        this.appendChild(clone);
        this.table = this.querySelector("tbody") ;
        this.API.getTournaments().then((res) => {
            this.tournaments = res ;
            this.tournaments.data.forEach(element => {
              let row = document.createElement('tr') ;
              let th = document.createElement('th') ;
              th.scope = 'row' ;
              th.innerText = element.uuid ;
              row.appendChild(th) ;
              let td = document.createElement('td') ;
              td.innerText = `${4 - element.spots}/4` ;
              row.appendChild(td) ;
              td = document.createElement('td') ;
              let join_button = document.createElement('button') ;
              join_button.innerHTML = element.spots ? 'Join' : 'Check'
              join_button.onclick = (e) => {join_tournament(element.uuid)} ;
              join_button.classList += "btn btn-block bg-dark text-white ps-4 pe-4" ;
              td.appendChild(join_button) ;
              row.appendChild(td) ;
              this.table.appendChild(row) ;
            }) ;
        });
    }
}

async function join_tournament(tournament_id) {
    navigateTo(`/tournament/${tournament_id}`) ;
}

window.customElements.define("join-page", JoinPage);
export { JoinPage };
