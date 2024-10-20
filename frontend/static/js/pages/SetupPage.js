import { hideToast, showToast } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

export class SetupPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("setup-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.fillDefaultValues();
    const fileUpload = this.querySelector(".file-upload");
    this.file = null;

    fileUpload.addEventListener("change", () => {
      if (fileUpload.files && fileUpload.files[0]) {
        const reader = new FileReader();
        const img = this.querySelector(".profile-pic");
        reader.onload = function (e) {
          img.src = e.target.result;
        };

        reader.readAsDataURL(fileUpload.files[0]);
        this.file = fileUpload.files[0];
      }
    });

    this.querySelector(".upload-button").addEventListener("click", function () {
      fileUpload.click();
    });

    const form = this.querySelector("form");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.submitForm(form);
    });
  }

  fillDefaultValues() {
    this.querySelector("#username").value = window.user.username;
    this.querySelector(".profile-pic").src = window.user.profile.avatar;
  }

  async submitForm(form) {
    try {
      hideToast("setup-errors");
      const formData = new FormData(form);
      if (this.file)
        formData.append("avatar", this.file);

      const response = await fetch("http://localhost:8000/api/auth/setup/", {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await response.json();

      if (data && data.success) {
        window.user = data.data;
        showToast(false, "Profile setup successfully");
        navigateTo("/home");
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }

  disconnectedCallback() {
    this.remove();
  }
}

customElements.define("setup-page", SetupPage);
