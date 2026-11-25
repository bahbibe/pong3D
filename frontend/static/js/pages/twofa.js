import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";

const view = () => html`
  <section class="d-flex">
    <div class="main">
      <main class="p-3">
        <div class="container">
          <div class="d-flex flex-column align-items-center justify-content-center">
            <h2 class="my-5 text-center">Two Factor Authentication</h2>
            <div class="col-10 col-md-5">
              <div class="mb-3">
                <label for="twofa-code" class="form-label">Two Factor Code</label>
                <input
                  type="text"
                  name="code"
                  id="twofa-code"
                  class="form-control form-control-lg"
                  placeholder="code"
                  value=""
                />
                <div class="form-text d-none text-danger"></div>
              </div>
              <div class="input-group mt-4">
                <button
                  id="verify-twofa"
                  type="button"
                  class="btn btn-lg btn-primary w-100 fs-6 fw-bold"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </section>
`;

class TwoFaPage extends Page {
  mount() {
    this.render(view());
    this.input = this.querySelector("#twofa-code");
    this.error = this.querySelector(".form-text");
    this.on(this.querySelector("#verify-twofa"), "click", () => this.verify());
    this.on(this.input, "keydown", (event) => {
      if (event.key === "Enter") this.verify();
    });
  }

  async verify() {
    const code = this.input.value.trim();
    this.error.classList.toggle("d-none", code !== "");
    if (code === "") {
      this.error.textContent = "Please enter the two factor code";
      return;
    }
    const result = await this.api.post("/api/auth/twofa/verify/", { code });
    if (!toastOnError(result)) return;
    await session.load();
    navigate("/home");
  }
}

customElements.define("two-fa-page", TwoFaPage);
