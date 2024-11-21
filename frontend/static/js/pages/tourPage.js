
import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { navigateTo } from "../router.js";

class TourPage extends AbstractPage {
    constructor() {
    super();
    this.API = new API();
    }

    create_tournament = () => {
        this.API.create_tournament().then((res) => {
          navigateTo(`/tournament/${res.data.uuid}`);
        });
    };

    connectedCallback() {
        const template = document.getElementById("tour-page");
        const clone = template.content.cloneNode(true);
        this.appendChild(clone);
        this.create_tour = this.querySelector("#create_tour") ;
        this.join_tour = this.querySelector("#join_tour") ;
        this.create_tour.onclick = (e) => {
            this.create_tournament();
        }
        this.join_tour.onclick = (e) => {
            navigateTo('/join') ;
        }
    }
}


window.customElements.define("tour-page", TourPage);
export { TourPage };
