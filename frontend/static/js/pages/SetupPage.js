import { ProfileFormPage } from "./ProfileFormPage.js";

export class SetupPage extends ProfileFormPage {
  static templateId = "setup-page";
  static formSelector = "form";
  static endpoint = "/api/auth/setup/";
  static method = "POST";
  static successMessage = "Profile setup successfully";
  static nextPath = "/home";
}

customElements.define("setup-page", SetupPage);
