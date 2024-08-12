import { AbstractPage } from "./AbstarctPage.js";

class ProfilePage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-profile");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const ctn = this.querySelector(".profile-content");
    // ctn.textContent = "HISTORY";
    const btns = this.querySelectorAll("input.switcher");
    btns.forEach(function(btn) {
      btn.addEventListener("click", function(e) {
        if(e.target.id === "friends")
          ctn.classList.add("d-none");
        else
        {
          ctn.classList.remove("d-none");
        }
      })
      
    }) 
  }
}

class mainNav extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("main-nav");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const toggler = this.querySelector(".toggler-btn");
    toggler.addEventListener("click", function () {
    document.querySelector("#sidebar").classList.toggle("collapsed");
    });

  }
}

window.customElements.define("user-profile", ProfilePage);
window.customElements.define("main-nav", mainNav);

export { ProfilePage }