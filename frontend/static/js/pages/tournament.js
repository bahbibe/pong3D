import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";

// A tournament game ends when a player reaches this score.
const WINNING_SCORE = 3;

const view = () => html`
  <main-nav></main-nav>
  <section>
    <div class="theme theme-dark" style="overflow-x: auto;">
      <div class="bracket disable-image">
        <div class="column one">
          <div class="round1 game1 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">1</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
          <div class="round1 game1 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">4</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
          <div class="round1 game2 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">2</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
          <div class="round1 game2 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">3</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
        </div>
        <div class="column two">
          <div class="round2 game3 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">1</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
          <div class="round2 game3 match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">2</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
        </div>
        <div class="column three">
          <div class="winner match winner-bottom">
            <div class="match-top team">
              <span class="image"></span>
              <span class="seed">5</span>
              <span class="name"></span>
              <span class="score">0</span>
            </div>
            <div class="match-lines">
              <div class="line one"></div>
              <div class="line two"></div>
            </div>
            <div class="match-lines alt">
              <div class="line one"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
`;

const winnerOf = (game) => {
  if (game.player1_score > game.player2_score) return 0;
  if (game.player1_score < game.player2_score) return 1;
  return null;
};

/**
 * The bracket of a tournament (/tournament/:tournament_id): two semi-finals
 * (.game1, .game2), the final (.game3) and the winner. Every message on the
 * tournament socket means it changed; when one of your games is ready, it
 * opens.
 */
class TournamentPage extends Page {
  mount() {
    this.render(view());
    const id = encodeURIComponent(this.params.tournament_id);
    this.socket(`/ws/tournament/${id}`, { onMessage: () => this.load() });
  }

  async load() {
    const id = this.params.tournament_id;
    const result = await this.api.get(`/api/game/get_tournament_games/${encodeURIComponent(id)}`);
    if (!toastOnError(result)) return;
    const games = result.data.data;
    const ordered = [
      ...games.filter((entry) => entry.t_round === 2).sort((a, b) => a.game.id - b.game.id),
      ...games.filter((entry) => entry.t_round === 1),
    ];
    for (const [index, { game }] of ordered.entries()) {
      const slots = this.querySelectorAll(`.game${index + 1}`);
      if (slots.length < 2) break;
      this.fillSlot(slots[0], game.player1, game.player1_score);
      this.fillSlot(slots[1], game.player2, game.player2_score);
      const winner = winnerOf(game);
      if (winner === 0) slots[1].classList.replace("winner-top", "winner-bottom");
      if (winner === 1) slots[0].classList.replace("winner-top", "winner-bottom");
      if (this.isMyGameToPlay(game)) {
        navigate(`/play/${encodeURIComponent(id)}/${game.id}`);
        return;
      }
    }
    const final = games.find((entry) => entry.t_round === 1)?.game;
    if (final && winnerOf(final) !== null) {
      const champion = winnerOf(final) === 0 ? final.player1 : final.player2;
      this.fillSlot(this.querySelector(".winner"), champion, "");
    }
  }

  isMyGameToPlay(game) {
    const me = session.user.username;
    return (
      game.player1 &&
      game.player2 &&
      (game.player1.username === me || game.player2.username === me) &&
      game.player1_score < WINNING_SCORE &&
      game.player2_score < WINNING_SCORE
    );
  }

  fillSlot(slot, player, score) {
    if (player) slot.classList.replace("winner-bottom", "winner-top");
    render(
      slot.querySelector(".image"),
      player ? html`<img src="${player.profile.avatar}" alt="" />` : html``,
    );
    slot.querySelector(".name").textContent = player?.username ?? "";
    slot.querySelector(".score").textContent = score ?? "0";
  }
}

customElements.define("tournament-display-page", TournamentPage);
