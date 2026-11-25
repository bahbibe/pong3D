import { html } from "../core/html.js";
import { Component } from "../core/page.js";
import { navigate } from "../core/router.js";

const view = () => html`
  <form class="input-group" id="search">
    <input
      class="form-control"
      type="search"
      placeholder="Search"
      aria-label="Search"
      data-search
    />
    <button class="input-group-text  d-lg-flex" aria-label="Search">
      <i class="fas fa-search" aria-hidden="true"></i>
    </button>
  </form>
`;

/** The search box in the nav: opens /search?q=... */
class SearchBar extends Component {
  mount() {
    this.render(view());
    const input = this.querySelector("[data-search]");
    this.on(this.querySelector("form#search"), "submit", (event) => {
      event.preventDefault();
      const query = input.value.trim();
      input.value = "";
      navigate(`/search?q=${encodeURIComponent(query)}`);
    });
  }
}

customElements.define("search-bar", SearchBar);
