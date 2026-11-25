import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";

const view = () => html`
  <main-nav></main-nav>
  <section>
    <div class="container-md p-4">
      <h1>Join a Tournament</h1>
      <table class="table text-center mt-4">
        <thead class="thead-dark">
          <tr>
            <th scope="col">Tournament Id</th>
            <th scope="col">Players Number</th>
            <th scope="col">Join a Tournament</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </section>
`;

const row = (tournament) => html`
  <tr>
    <th scope="row">${tournament.uuid}</th>
    <td>${4 - tournament.spots}/4</td>
    <td>
      <a
        href="/tournament/${tournament.uuid}"
        data-link
        class="btn btn-block bg-dark text-white ps-4 pe-4"
      >
        ${tournament.spots ? "Join" : "Check"}
      </a>
    </td>
  </tr>
`;

/** Open tournaments. */
class TournamentJoinPage extends Page {
  async mount() {
    this.render(view());
    const result = await this.api.get("/api/game/get_tournaments/");
    if (!toastOnError(result)) return;
    render(this.querySelector("tbody"), html`${result.data.data.map(row)}`);
  }
}

customElements.define("join-page", TournamentJoinPage);
