import { html } from "../core/html.js";
import { ProfileFormPage } from "./profile-form.js";

/** First login: pick a username and an avatar. */
class SetupPage extends ProfileFormPage {
  static view = () => html`
    <section class="d-flex">
      <div class="container">
        <div class="d-flex flex-column align-items-center justify-content-center">
          <h2 class="mt-5 text-center">Just a few more steps left</h2>
          <h2 class="mb-2 text-center">to start enjoying the PONG game!</h2>
          <form action="POST" class="col-10 col-md-5">
            <div class="avatar-wrapper">
              <img class="profile-pic" src="" alt="Your avatar" />
              <input class="file-upload d-none" name="avatar" type="file" accept="image/*" />
            </div>
            <div class="w-100 d-flex align-items-center mb-4">
              <button type="button" class="mx-auto upload-button btn btn-light">Upload</button>
            </div>
            <div class="mb-3">
              <label for="username" class="form-label">Username</label>
              <input
                type="text"
                name="username"
                id="username"
                class="form-control form-control-lg "
                placeholder="username"
                value=""
              />
            </div>
            <!--! ability to enable or disable 2fa from here  -->
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
                Let's play
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  `;
  static formSelector = "form";
  static endpoint = "/api/auth/setup/";
  static method = "POST";
  static successMessage = "Profile setup successfully";
  static nextPath = "/home";
}

customElements.define("setup-page", SetupPage);
