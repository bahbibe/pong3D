import { ProfileFormPage } from "./ProfileFormPage.js";

class SettingsPage extends ProfileFormPage {
  static templateId = "settings-page";
  static formSelector = "#settings-form";
  static endpoint = "/api/auth/settings/update/";
  static method = "PUT";
  static showEmail = true;
  static successMessage = "Settings updated successfully";
  static nextPath = "/profile";
}

window.customElements.define("settings-page", SettingsPage);

export { SettingsPage };
