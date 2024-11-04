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

    const first_name = this.querySelector("#firstName");

    const user = window.user;
    first_name.textContent = `${user.first_name}`;


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
    
    const links = this.querySelectorAll(".sidebar-link");

    links.forEach((link) => {
      if (window.path === link.getAttribute("href")) {
        this.activeLink = this.querySelector(`a[href="${window.path}"].sidebar-link`);
        this.activeLink.classList.add("active");
      }

    });


    this.addEventListener("click", this);
    
    

  }
  handleEvent(e) {
    this[`on${e.type}`](e)   
  }
  onclick(e) {
    e.preventDefault();
    this.logout(e);

  }


  logout(e) {
    e.preventDefault();
    if (!(e.target.id === "logout")) return;
    fetch("http://localhost:8000/api/auth/logout/", {
      method: "POST",
      credentials: "include",
    })
    .then((res) => {
      console.log("socket closed -> ", window.socket);
      if (window.socket) {
        window.socket.close();
      }
      window.user = null;
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