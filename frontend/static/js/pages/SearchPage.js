import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";
import { BASE_URL } from "../router.js";
class SearchPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.container = document.querySelector("#search-container");

    this.SearchedUser = localStorage.getItem("SearchedUser");
    this.found = false;
    if (this.SearchedUser) this.renderUser();
  }

  async renderUser() {
    try {
      console.log(this.SearchedUser);
      const response = await fetch(
        `${BASE_URL}/api/auth/users/?q=${this.SearchedUser}`,
        { credentials: "include" }
      );
      const data = await response.json();
      const users = data.data;
      if (response.ok) {
        users.forEach((user) => {
          this.container.innerHTML += `
          <div class=" secondary-bg box-sh-1 p-2 text-center rounded  mx-auto mx-md-0  me-md-3 mb-3" style="width: 160px; height: 140px;">
            <a class="font-monospace fw-bold" href='/friend/${user.profile.uuid}'>
              <div class="">
                <img class="img-fluid ratio ratio-1x1 rounded rounded-circle" src="${user.profile.avatar}" alt="" width="100" height="100" style="width: 100px; height: 100px">
              </div>
              <div class="my-2">
                <span class="font-monospace fw-bold">${user.username} </span>
              </div>
              </a>
            </div>
          `;
        });
      } else
        this.container.innerHTML = `<p class="fw-bold fs-1">User Not Fount!</p>`;
    } catch (error) {
      console.log(error);
    }
  }
}

class SearchBar extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-bar");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.form = this.querySelector("form#search");
    this.inputSearch = this.querySelector("[data-search]");

    this.form.addEventListener("submit", (e) => {
      e.preventDefault();
      console.log("searching");
      // window.SearchedUser = this.inputSearch.value;
      localStorage.setItem("SearchedUser", this.inputSearch.value);
      this.inputSearch.value = "";
      navigateTo("/search");
    });
  }
}

window.customElements.define("search-bar", SearchBar);
window.customElements.define("search-page", SearchPage);

export { SearchPage, SearchBar };
