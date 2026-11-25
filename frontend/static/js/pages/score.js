import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";
import { playAgain } from "../services/game.js";

const view = () => html`
  <main-nav></main-nav>
  <div class="min-vh-100 d-flex align-items-center justify-content-evenly flex-column">
    <div class="score score-board d-flex w-100 align-items-center justify-content-evenly">
      <div class="player player1 round-1"></div>
      <span id="player1_score">0</span>
      <span>-</span>
      <span id="player2_score">0</span>
      <div class="player player2 round-1"></div>
    </div>
    <div class="score score-board d-flex w-100 align-items-center justify-content-evenly">
      <a
        class="play px-3 py-1 fw-bold text-uppercase"
        style="color: var(--light); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);"
        href="/matchmaking"
        data-link
        >Play Random</a
      >

      <button
        type="button"
        id="invite_game"
        class="play px-3 py-1 fw-bold text-uppercase"
        style="color: var(--light); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);"
      >
        Play Again
      </button>
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
  </div>
`;

/** The result of a game (/score/:game_id; bot games pass the scores in the query). */
class ScorePage extends Page {
  async mount() {
    this.render(view());
    const again = this.querySelector("#invite_game");
    if (this.params.game_id === "bot") {
      this.show(1, session.user.profile.avatar, parseInt(this.query.get("player1_score"), 10) || 0);
      this.show(
        2,
        "/static/asset/images/robots_welcome.svg",
        parseInt(this.query.get("player2_score"), 10) || 0,
      );
      this.on(again, "click", () => navigate("/play/bot"));
      return;
    }
    const result = await this.api.get(
      `/api/game/get_game/${encodeURIComponent(this.params.game_id)}`,
    );
    if (!toastOnError(result)) return;
    const { game } = result.data;
    if (game.player1) this.show(1, game.player1.profile.avatar, game.player1_score);
    if (game.player2) this.show(2, game.player2.profile.avatar, game.player2_score);
    this.on(again, "click", () => playAgain(this.api, game.id));
  }

  show(side, avatar, points) {
    render(this.querySelector(`.player${side}`), html`<img src="${avatar}" alt="" />`);
    this.querySelector(`#player${side}_score`).textContent = points;
  }
}

customElements.define("score-page", ScorePage);
