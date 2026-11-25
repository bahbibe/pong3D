import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";

const view = () => html`
  <section>
    <main-nav></main-nav>
    <div class="container-md font-monospace">
      <h1 class="display-1 my-5">Leaderboard</h1>

      <div class="table-responsive">
        <table class="mytable">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Users</th>
              <th scope="col">Total</th>
              <th scope="col">Wins</th>
              <th scope="col" class="">Loses</th>
              <th scope="col">Ratio</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </section>
`;

const row = (entry, index) => html`
  <tr>
    <th scope="row">${index + 1}</th>
    <td>
      <div class="user-cell">
        <img src="${entry.user.avatar}" alt="" />
        <div class="username">${entry.user.username}</div>
      </div>
    </td>
    <td>${entry.total_games}</td>
    <td>${entry.total_wins}</td>
    <td>${entry.total_losses}</td>
    <td>${entry.ratio}</td>
  </tr>
`;

/** Every player, best ratio first. */
class RankingPage extends Page {
  async mount() {
    this.render(view());
    const result = await this.api.get("/api/game/leaderboard/");
    if (!toastOnError(result)) return;
    render(this.querySelector("tbody"), html`${result.data.users.map(row)}`);
  }
}

customElements.define("ranking-page", RankingPage);
