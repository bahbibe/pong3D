import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { overlay } from "../core/overlay.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";
import { toast } from "../core/toast.js";

// Same rule as the hint under the field: 8+ characters, a letter and a digit.
// The server runs the full password checks.
const PASSWORD_HINT = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

const view = () => html`
  <section>
    <div class="container-lg d-flex justify-content-center align-items-center text-black min-vh-100 font-monospace">
      <div class="col-lg-8 col-md-6 flex-column pe-5 left-box text-color ">
        <h1 class="rubik-glitch-regular title">PONG</h1>
        <p class="fs-1 text-light  pe-xxl-5 fw-medium">
          pong help you to enjoy the moment with your friend
        </p>
      </div>
      <div class="col-12 col-md-8 col-lg-5  box-padding rounded right-box glass-effect">
        <ul class="nav nav-pills nav-justified mb-3" id="ex1" role="tablist">
          <li class="nav-item" role="presentation">
            <a href="#" class="nav-link activeBtn fw-bold text-uppercase" id="tab-login" role="tab"
              aria-controls="pills-login" aria-selected="false" style="color: #fefefe;">Login</a>
          </li>
          <li class="nav-item" role="presentation">
            <a href="#" class="nav-link fw-bold text-uppercase" id="tab-register" role="tab"
              aria-controls="pills-register" aria-selected="true" style="color: #fefefe;">Register</a>
          </li>
        </ul>
        <div class="row align-items-center" id="login">
          <div class="mb-4">
            <h2 class="fw-bold" style="color: #110818;">Welcome Back</h2>
          </div>
          <form action="" method="post" id="login-form">
            <div class="input-group mb-3">
              <input aria-label="Email address" type="email" class="form-control form-control-lg bg-light fs-6" placeholder="Email address"
                data-email required />
            </div>
            <div class="input-group mb-5">
              <input aria-label="Password" type="password" class="form-control form-control-lg bg-light fs-6" placeholder="Password"
                data-password>
            </div>

            <div class="input-group mb-3">
              <button class="btn btn-lg w-100 fw-bold text-uppercase glass-effect" data-login type="submit"
                style="color: var(--darker)">Login</button>
            </div>
            <div class="input-group mb-3">
              <button class="btn btn-lg w-100 fw-bold text-uppercase glass-effect" type="button" id="intra"
                style="color: var(--darker)"><span class="me-2">Sign
                  In with </span><img src="/static/asset/images/42.svg" style="width:20px " alt="42">
              </button>
            </div>
          </form>
        </div>
        <div class="row align-items-center hidden" id="register">
          <form action="" method="POST" id="register-form">
            <div class="input-group mb-3">
              <input aria-label="First name" type="text" class="form-control form-control-lg" placeholder="First name" id="firstName"
                required />
            </div>
            <div class="input-group mb-3">
              <input aria-label="last name" type="text" class="form-control form-control-lg" placeholder="last name" id="lastName"
                required />
            </div>
            <div class="input-group mb-3">
              <input aria-label="username" type="text" class="form-control form-control-lg" placeholder="username" id="username" required
                name="username" />
            </div>
            <div class="input-group mb-3">
              <input aria-label="Email address" type="email" class="form-control form-control-lg bg-light fs-6" placeholder="Email address"
                id="email" required name="email" />
            </div>
            <div class="input-group mb-3">
              <input aria-label="Password" type="password" class="form-control form-control-lg bg-light fs-6" placeholder="Password"
                id="password" required />
            </div>
            <div class="input-group mb-3">
              <input aria-label="Confirm Password" type="password" class="form-control form-control-lg bg-light fs-6" placeholder="Confirm Password"
                id="confirm-password" required />
            </div>

            <p class="lengthPassword d-none" style="font-size: 12px; color: red;">The password must have at least 8
              characters, a letter and a number</p>

            <div class="input-group mb-3">
              <button class="btn btn-lg w-100 fw-bold text-uppercase glass-effect" data-register
                style="color: var(--darker)">Register</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </div>
  </section>
`;

class LoginPage extends Page {
  mount() {
    this.render(view());
    this.hint = this.querySelector(".lengthPassword");
    const tab = (name) => (event) => {
      event.preventDefault();
      this.showTab(name);
    };
    this.on(this.querySelector("#tab-login"), "click", tab("login"));
    this.on(this.querySelector("#tab-register"), "click", tab("register"));
    this.on(this.querySelector("#login-form"), "submit", (event) => {
      event.preventDefault();
      this.login();
    });
    this.on(this.querySelector("#register-form"), "submit", (event) => {
      event.preventDefault();
      this.register();
    });
    this.on(this.querySelector("#intra"), "click", () => this.intraLogin());
    // The password hint shows while a password field has the focus. Focus
    // moving to a button keeps it as it is: hiding it there would move the
    // button away under the pointer mid-click.
    this.on(this, "focusin", (event) => {
      if (event.target.tagName !== "INPUT") return;
      const isPassword = ["password", "confirm-password"].includes(event.target.id);
      this.hint.classList.toggle("d-none", !isPassword);
    });
    this.on(this, "input", (event) => {
      if (event.target.id !== "password") return;
      this.hint.style.color = PASSWORD_HINT.test(event.target.value) ? "green" : "red";
    });
  }

  showTab(name) {
    const login = name === "login";
    this.querySelector("#login").classList.toggle("hidden", !login);
    this.querySelector("#register").classList.toggle("hidden", login);
    this.querySelector("#tab-login").classList.toggle("activeBtn", login);
    this.querySelector("#tab-register").classList.toggle("activeBtn", !login);
  }

  async login() {
    toast.hide();
    overlay.show();
    const result = await this.api.post(
      "/api/auth/login/",
      {
        email: this.querySelector("[data-email]").value,
        password: this.querySelector("[data-password]").value,
      },
      { auth: false },
    );
    if (result.ok) await session.load();
    overlay.hide();
    if (!toastOnError(result)) return;
    navigate(session.tfaPending ? "/twofa" : "/home");
  }

  async register() {
    toast.hide();
    const field = (id) => this.querySelector(`#register-form #${id}`);
    const password = field("password").value;
    if (password !== field("confirm-password").value || !PASSWORD_HINT.test(password)) {
      toast.error("passwords do not match or password is not valid");
      field("password").value = "";
      field("confirm-password").value = "";
      return;
    }
    const result = await this.api.post(
      "/api/auth/register/",
      {
        first_name: field("firstName").value,
        last_name: field("lastName").value,
        username: field("username").value,
        email: field("email").value,
        password,
        confirm_password: field("confirm-password").value,
      },
      { auth: false },
    );
    if (!toastOnError(result)) return;
    this.querySelector("#register-form").reset();
    this.showTab("login");
    toast.success(result.message);
  }

  async intraLogin() {
    overlay.show();
    const result = await this.api.get("/api/auth/intra/", { auth: false });
    if (result.ok) {
      window.location.replace(result.data.url);
      return;
    }
    overlay.hide();
    toastOnError(result);
  }
}

customElements.define("login-page", LoginPage);
