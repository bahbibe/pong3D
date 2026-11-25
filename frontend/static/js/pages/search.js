import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";

const view = () => html`
  <section>
    <main-nav></main-nav>
    <div class="container p-3">
      <div class="row flex-column flex-md-row mt-4" id="search-container"></div>
    </div>
  </section>
`;

const card = (user) => html`
  <div
    class="secondary-bg box-sh-1 p-2 text-center rounded mx-auto mx-md-0 me-md-3 mb-3"
    style="width: 160px; height: 140px;"
  >
    <a class="font-monospace fw-bold" href="/friend/${user.profile.uuid}" data-link>
      <div>
        <img
          class="img-fluid ratio ratio-1x1 rounded rounded-circle"
          src="${user.profile.avatar}"
          alt=""
          width="100"
          height="100"
          style="width: 100px; height: 100px"
        />
      </div>
      <div class="my-2">
        <span class="font-monospace fw-bold">${user.username}</span>
      </div>
    </a>
  </div>
`;

/** Users matching ?q= (the nav search bar opens it). */
class SearchPage extends Page {
  async mount() {
    this.render(view());
    const query = this.query.get("q")?.trim();
    if (!query) return;
    const result = await this.api.get(`/api/auth/users/?q=${encodeURIComponent(query)}`);
    if (!toastOnError(result)) return;
    render(
      this.querySelector("#search-container"),
      result.data.length
        ? html`${result.data.map(card)}`
        : html`<p class="fw-bold fs-1">No user found</p>`,
    );
  }
}

customElements.define("search-page", SearchPage);
