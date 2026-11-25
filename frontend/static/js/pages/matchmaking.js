import { html } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";

const view = () => html`
  <section class="">
    <main-nav class="position-absolute w-100"></main-nav>
    <div class="d-flex min-vh-100 flex-column align-items-center justify-content-center">
      <h1 id="loader-message" class="mx-auto"></h1>
      <div class="loader mx-auto"></div>
      <a
        class="play px-3 py-1 fw-bold text-uppercase"
        style="color: var(--light); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);"
        href="/home"
        data-link
        >Leave</a
      >
    </div>
  </section>
`;

/** Waits in the matchmaking queue, then opens the game it finds. */
class MatchmakingPage extends Page {
  mount() {
    this.render(view());
    const message = this.querySelector("#loader-message");
    message.textContent = "Looking for a match...";
    this.socket("/ws/matchmaking", {
      onMessage: (data) => {
        if (data.type !== "game_found") return;
        message.textContent = "Match Found!";
        this.querySelector(".loader").style.display = "none";
        this.timeout(() => navigate(`/play/${data.game_id}`), 2000);
      },
    });
  }
}

customElements.define("matchmaking-page", MatchmakingPage);
