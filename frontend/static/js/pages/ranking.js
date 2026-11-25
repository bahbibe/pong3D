import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";

const view = () => html`
  <section>
    <main-nav></main-nav>
    <div class="container-md font-monospace">
      <h1 class="display-1 my-5">Leaderboard</h1>

      <nav
        class="ranking-pager d-flex justify-content-between align-items-center my-3"
        aria-label="Leaderboard pages"
      ></nav>

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

const row = (entry) => html`
  <tr>
    <th scope="row">${entry.rank}</th>
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

const pageLink = (page, label, disabled) => html`
  <li class="page-item ${disabled ? "disabled" : ""}">
    <a class="page-link" href="/ranking?page=${page}" data-link aria-disabled="${disabled}"
      >${label}</a
    >
  </li>
`;

const pager = (page, pages, me) => html`
  <span class="your-rank">${me ? `Your rank: #${me.rank}` : ""}</span>
  <ul class="pagination m-0">
    ${pageLink(page - 1, "Previous", page <= 1)}
    <li class="page-item disabled">
      <span class="page-link page-position">${page} / ${pages}</span>
    </li>
    ${pageLink(page + 1, "Next", page >= pages)}
  </ul>
`;

/** Every player, best ratio first, 20 per page (?page=). */
class RankingPage extends Page {
  async mount() {
    this.render(view());
    const asked = Number.parseInt(this.query.get("page"), 10) || 1;
    const result = await this.api.get(`/api/game/leaderboard/?page=${asked}`);
    if (!toastOnError(result)) return;
    const { users, page, pages, me } = result.data;
    render(this.querySelector("tbody"), html`${users.map(row)}`);
    render(this.querySelector(".ranking-pager"), pager(page, pages, me));
  }
}

customElements.define("ranking-page", RankingPage);
