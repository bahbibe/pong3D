import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";
import { toast } from "../core/toast.js";

/**
 * Shared logic of the Setup (first login) and Settings pages: avatar
 * preview, the profile form and the 2FA enable/confirm/disable flow.
 * Subclasses set the static config below.
 */
export class ProfileFormPage extends Page {
  static view = () => html``;
  static formSelector = "form";
  static endpoint = "";
  static method = "POST";
  static showEmail = false;
  static successMessage = "";
  static nextPath = "/home";

  get config() {
    return this.constructor;
  }

  mount() {
    this.render(this.config.view());
    this.modal = this.querySelector("#twoFaModal");
    this.modalOpen = false;
    this.on(this.modal, "shown.bs.modal", () => (this.modalOpen = true));
    this.on(this.modal, "hidden.bs.modal", () => (this.modalOpen = false));
    this.fillDefaultValues();

    this.file = null;
    const fileUpload = this.querySelector(".file-upload");
    this.on(fileUpload, "change", () => this.previewAvatar(fileUpload.files?.[0]));
    this.on(this.querySelector(".upload-button"), "click", () => fileUpload.click());

    this.on(this.querySelector("#enable-2fa"), "click", () => this.enable2FA());
    this.on(this.querySelector("#disable-2fa"), "click", () => this.disable2FA());
    this.on(this.querySelector("#confirm-2fa"), "click", () => this.confirm2FA());
    // The modal sits inside the profile form (nested forms are invalid HTML):
    // Enter in the code field confirms the code, not the profile form.
    this.on(this.querySelector("#twofa-code"), "keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      this.confirm2FA();
    });

    const form = this.querySelector(this.config.formSelector);
    this.on(form, "submit", (event) => {
      event.preventDefault();
      this.submitForm(form);
    });

    this.show2FAState(session.user.profile.is_tfa_enabled);
  }

  unmount() {
    // Leaving the page with the modal open would leave its backdrop behind.
    bootstrap.Modal.getInstance(this.modal)?.dispose();
    document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }

  fillDefaultValues() {
    const user = session.user;
    this.querySelector("#username").value = user.username;
    const pic = this.querySelector(".profile-pic");
    pic.src = user.profile.avatar;
    pic.alt = "Your avatar";
    if (this.config.showEmail) this.querySelector("#email").value = user.email;
  }

  previewAvatar(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      this.querySelector(".profile-pic").src = event.target.result;
    };
    reader.readAsDataURL(file);
    this.file = file;
  }

  show2FAState(enabled) {
    this.querySelector("#enable-2fa").classList.toggle("d-none", enabled);
    this.querySelector("#disable-2fa").classList.toggle("d-none", !enabled);
  }

  async submitForm(form) {
    toast.hide();
    const body = new FormData(form);
    if (this.file) body.append("avatar", this.file);
    const send = this.config.method === "PUT" ? this.api.put : this.api.post;
    const result = await send(this.config.endpoint, body);
    if (!toastOnError(result)) return;
    session.setUser(result.data);
    toast.success(this.config.successMessage);
    navigate(this.config.nextPath);
  }

  async enable2FA() {
    const result = await this.api.post("/api/auth/twofa/enable/");
    if (!toastOnError(result)) return;
    bootstrap.Modal.getOrCreateInstance(this.modal).show();
    const qrCode = this.querySelector("#qr-code");
    qrCode.src = result.data.image;
    qrCode.parentElement.classList.remove("d-none");
  }

  async confirm2FA() {
    const error = this.querySelector("#twoFaModal .form-text");
    const code = this.querySelector("#twofa-code").value.trim();
    error.classList.toggle("d-none", code !== "");
    if (code === "") {
      error.textContent = "Please enter the two factor code";
      return;
    }
    const result = await this.api.post("/api/auth/twofa/confirm/", { code });
    if (!toastOnError(result)) return;
    toast.success("2FA enabled successfully");
    this.closeModal();
    session.user.profile.is_tfa_enabled = true;
    this.show2FAState(true);
  }

  closeModal() {
    const modal = bootstrap.Modal.getInstance(this.modal);
    if (!modal) return;
    // Bootstrap ignores hide() while the opening animation runs.
    if (this.modalOpen) modal.hide();
    else this.on(this.modal, "shown.bs.modal", () => modal.hide(), { once: true });
  }

  async disable2FA() {
    // The server asks for a current code before it turns 2FA off.
    const code = window.prompt("Enter the code from your authenticator app to disable 2FA");
    if (code === null) return;
    if (code.trim() === "") {
      toast.error("Please enter the two factor code");
      return;
    }
    const result = await this.api.post("/api/auth/twofa/disable/", { code: code.trim() });
    if (!toastOnError(result)) return;
    toast.success("2FA disabled successfully");
    session.user.profile.is_tfa_enabled = false;
    this.show2FAState(false);
  }
}
