import { hideToast, showToast } from "../helpers.js";
import { navigateTo, BASE_URL } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

/**
 * Shared logic of the Setup (first login) and Settings pages: avatar
 * preview, profile form submit and the 2FA enable/confirm/disable flow.
 * Subclasses set the static config below.
 */
export class ProfileFormPage extends AbstractPage {
  static templateId = "";
  static formSelector = "form";
  static endpoint = "";
  static method = "POST";
  static showEmail = false;
  static successMessage = "";
  static nextPath = "/home";

  get config() {
    return this.constructor;
  }

  connectedCallback() {
    const template = document.getElementById(this.config.templateId);
    this.appendChild(template.content.cloneNode(true));

    this.fillDefaultValues();
    this.file = null;
    const fileUpload = this.querySelector(".file-upload");
    fileUpload.addEventListener("change", () => {
      const file = fileUpload.files && fileUpload.files[0];
      if (!file) return;
      const reader = new FileReader();
      const img = this.querySelector(".profile-pic");
      reader.onload = (e) => {
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
      this.file = file;
    });
    this.querySelector(".upload-button").addEventListener("click", () => fileUpload.click());

    this.querySelector("#enable-2fa").addEventListener("click", () => this.enable2FA());
    this.querySelector("#disable-2fa").addEventListener("click", () => this.disable2FA());
    // Bound once here: binding it in enable2FA added one more listener (and
    // one more confirm request) every time the modal was opened.
    this.querySelector("#confirm-2fa").addEventListener("click", () => this.confirm2FA());
    this.querySelector("#towfamodalform").addEventListener("submit", (e) => e.preventDefault());

    const form = this.querySelector(this.config.formSelector);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      this.submitForm(form);
    });

    this.show2FAState(window.user.profile.is_tfa_enabled);
  }

  fillDefaultValues() {
    this.querySelector("#username").value = window.user.username;
    const pic = this.querySelector(".profile-pic");
    pic.src = window.user.profile.avatar;
    pic.alt = "Your avatar";
    if (this.config.showEmail) this.querySelector("#email").value = window.user.email;
  }

  show2FAState(enabled) {
    this.querySelector("#enable-2fa").classList.toggle("d-none", enabled);
    this.querySelector("#disable-2fa").classList.toggle("d-none", !enabled);
  }

  async postJSON(path, body) {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return response.json();
  }

  async submitForm(form) {
    try {
      hideToast();
      const formData = new FormData(form);
      if (this.file) formData.append("avatar", this.file);
      const response = await fetch(`${BASE_URL}${this.config.endpoint}`, {
        method: this.config.method,
        body: formData,
        credentials: "include",
      });
      const data = await response.json();
      if (data && data.success) {
        window.user = data.data;
        showToast(false, this.config.successMessage);
        navigateTo(this.config.nextPath);
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      console.error(err);
      showToast(true);
    }
  }

  async enable2FA() {
    try {
      const data = await this.postJSON("/api/auth/twofa/enable/");
      if (!data || !data.success) {
        showToast(true, data.message, data.errors);
        return;
      }
      bootstrap.Modal.getOrCreateInstance(this.querySelector("#twoFaModal")).show();
      const qrCode = this.querySelector("#qr-code");
      qrCode.src = data.data.image;
      qrCode.parentElement.classList.remove("d-none");
    } catch (err) {
      showToast(true);
    }
  }

  async confirm2FA() {
    const error = this.querySelector("#twoFaModal .form-text");
    error.classList.add("d-none");
    const code = this.querySelector("#twofa-code").value.trim();
    if (code === "") {
      error.textContent = "Please enter the two factor code";
      error.classList.remove("d-none");
      return;
    }
    try {
      const data = await this.postJSON("/api/auth/twofa/confirm/", { code });
      if (data && data.success) {
        showToast(false, "2FA enabled successfully");
        bootstrap.Modal.getInstance(this.querySelector("#twoFaModal"))?.hide();
        window.user.profile.is_tfa_enabled = true;
        this.show2FAState(true);
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }

  async disable2FA() {
    // The server asks for a current code before it turns 2FA off.
    const code = window.prompt("Enter the code from your authenticator app to disable 2FA");
    if (code === null) return;
    if (code.trim() === "") {
      showToast(true, "Please enter the two factor code");
      return;
    }
    try {
      const data = await this.postJSON("/api/auth/twofa/disable/", { code: code.trim() });
      if (data && data.success) {
        showToast(false, "2FA disabled successfully");
        window.user.profile.is_tfa_enabled = false;
        this.show2FAState(false);
      } else {
        showToast(true, data.message, data.errors);
      }
    } catch (err) {
      showToast(true);
    }
  }
}
