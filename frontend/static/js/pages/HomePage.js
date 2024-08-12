import { AbstractPage } from "./AbstarctPage.js";

class HomePage extends AbstractPage {
  constructor() {
    super();
    // this.ws.connect()
  }

  connectedCallback() {
    const template = document.getElementById("home-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    // this.notify();
  }
}
class AsideNav extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("aside-nav");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.addEventListener("click" ,function(e){
      e.preventDefault();
      const activeLink = this.querySelector(".active");
      activeLink.classList.remove("active");
      console.log("========>", activeLink);
      e.target.classList.add("active");
      console.log(e.target);

    })
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
  }
}class User extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-info");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("home-page", HomePage);
window.customElements.define("aside-nav", AsideNav);
window.customElements.define("search-bar", SearchBar);
window.customElements.define("user-info", User);

export { HomePage }