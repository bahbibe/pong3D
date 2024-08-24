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

    const NavLinks = this.querySelectorAll("a.sidebar-link");

    // console.log(NavLinks);
    let activeLink = this.querySelector("a.sidebar-link.active");
    NavLinks.forEach(function(link) {
      link.addEventListener("click" ,function(e) {
        // e.preventDefault();
        console.log("Active Link: " , activeLink);
        activeLink.classList.remove("active");
        console.log(activeLink);
        link.classList.add("active");
        activeLink = link;
        console.log("test===>", activeLink);
        
        console.log("clicked link");
      })
      
    });
      // console.log("========>", activeLink);
      // console.log(e.target);

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