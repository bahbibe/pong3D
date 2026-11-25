import { html } from "../core/html.js";
import { ProfileFormPage } from "./profile-form.js";

class SettingsPage extends ProfileFormPage {
  static view = () => html`
    <section>
      <main-nav></main-nav>
      <div class="container">
        <div class="d-flex flex-column align-items-center justify-content-center">
          <form id="settings-form" action="" class="col-10 col-md-5  ">
            <div class="avatar-wrapper">
              <img class="profile-pic" src="" alt="Your avatar" />
              <input class="file-upload d-none" name="avatar" type="file" accept="image/*" />
            </div>
            <div class="w-100 d-flex align-items-center mb-4">
              <button type="button" class="mx-auto upload-button btn btn-light">Upload</button>
            </div>
            <div class="mb-3">
              <label for="username" class="form-label fw-bold">Username</label>
              <input
                type="text"
                name="username"
                id="username"
                class="form-control form-control-lg  mb-2"
                placeholder="username"
                value=""
              />
              <label for="email" class="form-label fw-bold">email</label>
              <input
                type="email"
                name="email"
                id="email"
                class="form-control form-control-lg mb-2"
                placeholder="email"
                value=""
              />
              <label for="password" class="form-label fw-bold">New Password</label>
              <input
                type="password"
                name="password"
                id="password"
                class="form-control form-control-lg mb-2"
                placeholder="new password"
                value=""
                autocomplete="new-password"
              />
              <label for="confirm_password" class="form-label fw-bold">Confirm Password</label>
              <input
                type="password"
                name="confirm_password"
                id="confirm_password"
                class="form-control form-control-lg mb-2"
                placeholder="confirm password"
                value=""
                autocomplete="new-password"
              />
              <label for="current_password" class="form-label fw-bold">Current Password</label>
              <input
                type="password"
                name="current_password"
                id="current_password"
                class="form-control form-control-lg mb-2"
                placeholder="needed to change email or password"
                value=""
                autocomplete="current-password"
              />
            </div>
            <div class="w-100 d-flex">
              <button type="button" id="disable-2fa" class="btn btn-outline-danger mx-auto d-none">
                Disable 2FA
              </button>
              <button type="button" id="enable-2fa" class="btn btn-outline-light mx-auto">
                Enable 2FA
              </button>
              <div id="towfamodalform">
                <div
                  class="modal fade"
                  id="twoFaModal"
                  data-bs-backdrop="static"
                  data-bs-keyboard="false"
                  tabindex="-1"
                  role="dialog"
                  aria-labelledby="twoFaModalTitle"
                  aria-hidden="true"
                >
                  <div class="modal-dialog modal-dialog-centered" role="document">
                    <div class="modal-content text-bg-dark">
                      <div class="modal-header">
                        <h5 class="modal-title" id="twoFaModalTitle">Enable 2FA</h5>
                        <button
                          type="button"
                          class="close btn btn-dark"
                          data-bs-dismiss="modal"
                          aria-label="Close"
                        >
                          <span aria-hidden="true">&times;</span>
                        </button>
                      </div>
                      <div class="modal-body text-bg-dark">
                        <div class="d-none d-flex flex-column justify-content-center">
                          <img
                            src=""
                            alt="Qr code"
                            id="qr-code"
                            class="align-self-center"
                            style="width: 300px; height: 300px;"
                          />
                          <div class="mt-3">
                            <label for="twofa-code" class="form-label">Two Factor Code</label>
                            <input
                              type="text"
                              name="code"
                              id="twofa-code"
                              class="form-control form-control-lg "
                              placeholder="code"
                              value=""
                            />
                            <div class="form-text d-none text-danger"></div>
                          </div>
                        </div>
                      </div>
                      <div class="modal-footer text-bg-dark">
                        <button type="button" class="btn btn-primary" id="confirm-2fa">
                          Confirm
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="input-group mt-4">
              <button type="submit" class="btn btn-lg btn-primary w-100 fs-6 fw-bold">
                Update
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  `;
  static formSelector = "#settings-form";
  static endpoint = "/api/auth/settings/update/";
  static method = "PUT";
  static showEmail = true;
  static successMessage = "Settings updated successfully";
  static nextPath = "/profile";
}

customElements.define("settings-page", SettingsPage);
