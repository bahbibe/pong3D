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
    this.form.addEventListener("submit", this);
  }
  handleEvent(e) {
    e.preventDefault();
    this[`on${e.type}`](e);

}
onsubmit(e) {

  const user = this.querySelector("[data-search]");
  const url = `http://localhost:8000/api/auth/users/`

  fetch(url, {
    credentials: "include",
  }
).then(rep => rep.json())
.then(data => {
      navigateTo(`/search`);
      console.log(data);
    })
    .catch(error => console.log("error:"));
  } 
}

window.customElements.define("search-page", SearchPage);

window.customElements.define("search-bar", SearchBar);

export { SearchPage }