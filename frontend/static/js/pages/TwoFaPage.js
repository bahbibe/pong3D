import { showToast } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

export class TwoFaPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("twofa-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.querySelector("#verify-twofa").addEventListener('click', () => {
      this.verifyTwoFa();
    });
  }

  async verifyTwoFa() {
    const error = this.querySelector(".form-text");
    error.classList.add("d-none");
    const code = this.querySelector("#twofa-code").value;
    if (code.trim() === "") {
      error.innerHTML = "Please enter the two factor code";
      error.classList.remove("d-none");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/auth/twofa/verify/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();
      if (data && data.success) {
        navigateTo("/home");
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }
}

customElements.define('two-fa-page', TwoFaPage);