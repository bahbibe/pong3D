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

    this.querySelector("#enable-2fa").addEventListener("click", () => {
      this.enable2FA();
    });

    this.querySelector("#disable-2fa").addEventListener("click", () => {
      this.disable2FA();
    });

    const form = this.querySelector("form");
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.submitForm(form);
    });

    if (window.user.profile.is_tfa_enabled) {
      this.querySelector("#enable-2fa").classList.add("d-none");
      this.querySelector("#disable-2fa").classList.remove("d-none");
    } else {
      this.querySelector("#enable-2fa").classList.remove("d-none");
      this.querySelector("#disable-2fa").classList.add("d-none");
    }

    this.querySelector("#towfamodalform").addEventListener("submit", (e) => { e.preventDefault(); });
  }

  fillDefaultValues() {
    this.querySelector("#username").value = window.user.username;
    this.querySelector(".profile-pic").src = window.user.profile.avatar;
  }

  async submitForm(form) {
    try {
      hideToast();
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

  async enable2FA() {
    try {
      const response = await fetch("http://localhost:8000/api/auth/twofa/enable/", {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();
      if (data && data.success) {
        const twoFaModal = this.querySelector("#twoFaModal");
        const modal = new bootstrap.Modal(twoFaModal);
        modal.show();
        const qrCode = this.querySelector("#qr-code");
        qrCode.src = data.data.image;
        qrCode.parentElement.classList.remove("d-none");
        this.querySelector("#confirm-2fa").addEventListener("click", () => this.confirm2FA());
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }

  async confirm2FA() {
    const error = this.querySelector(".form-text");
    error.classList.add("d-none");
    const code = this.querySelector("#twofa-code").value;
    if (code.trim() === "") {
      error.innerHTML = "Please enter the two factor code";
      error.classList.remove("d-none");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/auth/twofa/confirm/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      const data = await response.json();
      if (data && data.success) {
        showToast(false, "2FA enabled successfully");
        const twoFaModal = this.querySelector("#twoFaModal");
        const modal = bootstrap.Modal.getInstance(twoFaModal);
        modal.hide();
        this.querySelector("#enable-2fa").classList.add("d-none");
        this.querySelector("#disable-2fa").classList.remove("d-none");
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }

  async disable2FA() {
    try {
      const response = await fetch("http://localhost:8000/api/auth/twofa/disable/", {
        method: "POST",
        credentials: "include",
      });

      const data = await response.json();
      if (data && data.success) {
        showToast(false, "2FA disabled successfully");
        this.querySelector("#enable-2fa").classList.remove("d-none");
        this.querySelector("#disable-2fa").classList.add("d-none");
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
