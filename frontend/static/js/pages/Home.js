import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class Home extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-home");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    window.active = this.querySelector("a#profile");
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
    if (window.path !== "/search") {
      this.activeLink = this.querySelector(`a[href="${window.path}"].sidebar-link`);
      this.activeLink.classList.add("active");
    }

    this.addEventListener("click", this.handleevent);
    
    

  }
  handleevent(e) {
    this[`on${e.type}`](e)   
  }
  onclick(e) {
    e.preventDefault();
    // this.linkActive(e);
    this.logout(e);

  }
  // linkActive(e) {
  //   if (!(e.target.classList.contains("sidebar-link"))) return

  //   // if (e.target.classList.contains("active")) return;
  //   // console.log(this.activeLink);
  //   // console.log(e.target);
  //   // this.activeLink.classList.remove("active");
  //   this.active = e.target;
  //   e.target.classList.add("active");
  //   console.log("Target classList",e.target.classList);
  // }
  logout(e) {
    e.preventDefault();
    if (!(e.target.id === "logout")) return;
    fetch("http://localhost:8000/api/auth/logout/", {
      method: "POST",
      credentials: "include",
    })
    .then((res) => {
      if (res.status === 200) {
        navigateTo("/login");
      }
    })
    .catch((err) => {
      console.log(err);
  });
}

}


window.customElements.define("user-home", Home);
window.customElements.define("aside-nav", AsideNav);

export { Home }