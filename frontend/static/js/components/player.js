import { html } from "../core/html.js";

/** One finished game, seen from game.user (left) against game.player. */
export const historyRow = (game) => html`
  <div class="row mt-3 p-1 mb-1 glass-effect">
    <div class="col-4 my-auto p-0">
      <div class="d-md-flex align-items-center">
        <img
          src="${game.user.profile.avatar}"
          class="img-fluid rounded-circle d-none d-md-block"
          width="40"
          style="width: 40px; height: 40px"
          alt=""
        />
        <div class="ps-2">
          <span class="fw-bold text-capitalize">${game.user.username}</span>
        </div>
      </div>
    </div>
    <div class="col-2 col-md-2 my-auto text-center">
      <span class="result fw-bolder">${game.user_score}:${game.player_score}</span>
    </div>
    <div class="col-4 my-auto p-0 text-center">
      <div class="d-md-flex justify-content-center align-items-center">
        <div class="pe-2">
          <span class="fw-bold text-capitalize">${game.player.username}</span>
        </div>
        <img
          src="${game.player.profile.avatar}"
          class="img-fluid rounded-circle d-none d-md-block"
          width="40"
          style="width: 40px; height: 40px"
          alt=""
        />
      </div>
    </div>
    <div class="col-2 my-auto text-center">
      <span class="result h3" aria-label="${game.is_user_winner ? "WIN" : "LOSE"}">
        ${game.is_user_winner ? "🏆" : "😓"}
      </span>
    </div>
  </div>
`;

/** Games whose opponent account was deleted have no player to show. */
export const playableHistory = (games) => games.filter((game) => game.user && game.player);

/** Fill the four stat cards (.total, .wins, .losses, .ratio) in `root`. */
export const showStats = (root, stats) => {
  root.querySelector(".total").textContent = `${stats.total_games} Matches`;
  root.querySelector(".wins").textContent = `${stats.total_wins} Wins`;
  root.querySelector(".losses").textContent = `${stats.total_losses} Losses`;
  root.querySelector(".ratio").textContent = `${stats.ratio}%`;
};
