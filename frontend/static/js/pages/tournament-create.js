import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";

const view = () => html`
  <main-nav></main-nav>
  <section>
    <div class="container-md p-4 p-md-0">
      <h1 class="display-1 my-5">Tournament</h1>
      <div class="row align-items-center justify-content-evenly">
        <div class="secondary-bg p-2 tourCard tourCardBgImg CardBgImg1 mb-3 mb-md-0">
          <div class="overlay-card"></div>
          <button id="create_tour" href="#" class="btn btn-block btn-primary" style="z-index: 10;">
            Create Tournament
          </button>
        </div>
        <div class="secondary-bg tourCard tourCardBgImg CardBgImg2">
          <div class="overlay-card"></div>
          <button id="join_tour" href="#" class="btn btn-block btn-primary" style="z-index: 10;">
            Join Tournament
          </button>
        </div>
      </div>
    </div>
  </section>
`;

/** Create a tournament or go to the list of open ones. */
class TournamentCreatePage extends Page {
  mount() {
    this.render(view());
    this.on(this.querySelector("#create_tour"), "click", () => this.create());
    this.on(this.querySelector("#join_tour"), "click", () => navigate("/join"));
  }

  async create() {
    const result = await this.api.post("/api/game/create_tournament/");
    if (toastOnError(result)) navigate(`/tournament/${result.data.data.uuid}`);
  }
}

customElements.define("tour-page", TournamentCreatePage);
