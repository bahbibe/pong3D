import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class SearchPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.container = document.querySelector("#search-container");
    console.log(window.SearchedUser);
    this.randerUser();
  }
  randerUser() {

      const url = `http://localhost:8000/api/auth/users/`
    
      fetch(url, {
        credentials: "include",
      }
    ).then(rep => rep.json())
    .then(data => {
          data.data.filter((user) => {
            if (window.SearchedUser  && window.SearchedUser !== window.user.data.username &&  user.username === window.SearchedUser)
            {
              this.container.innerHTML = `
              <div class="secondary-bg box-sh-1 p-2 text-center rounded mx-auto mx-md-0" style="width: 160px; height: 140px;">
                        <div class="img ">
                          <img class="img-fluid rounded rounded-circle" src="${user.profile.avatar}" alt="" width="100" height="100">
                        </div>
                        <div class="my-2">
                          <span class="font-monospace fw-bold">${user.username}</span>
                        </div>
              </div>
              `
            }
          })
        })
        .catch(error => console.log("error:", error));
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
      window.SearchedUser = this.inputSearch.value;
      console.log("====> SearchedUser: ", window.SearchedUser);
      this.inputSearch.value = "";
      navigateTo("/search");
    });
  }
}

window.customElements.define("search-bar", SearchBar);
window.customElements.define("search-page", SearchPage);

export { SearchPage , SearchBar}