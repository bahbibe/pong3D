import { hideToast, showOverlay, hideOverlay, showToast } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";



class LoginPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("login-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    this.firstName = this.querySelector("#firstName");
    this.lastName = this.querySelector("#lastName");
    this.password = this.querySelector("#password");
    this.confirmPassword = this.querySelector("#confirm-password");
    this.email = this.querySelector("#email");

    this.lengthPassword = this.querySelector(".lengthPassword");
    const logninBtn = this.querySelector("[data-login]");
    this.loginForm = this.querySelector("#login-form");
    this.registerForm = this.querySelector("#register-form");
    this.intra = this.querySelector("#intra");


    // console.log(form);
    this.loginForm.addEventListener('submit', this);
    this.registerForm.addEventListener('submit', this);

    this.isValidPassword = false;


    const registerBtn = this.querySelector("#tab-register");
    const loginBtn = this.querySelector("#tab-login");
    const boxLogin = this.querySelector("#login");
    const boxRegister = this.querySelector("#register");

    this.switcher(registerBtn, loginBtn, boxRegister, boxLogin);
    this.switcher(loginBtn, registerBtn, boxLogin, boxRegister);

    this.intra.addEventListener('click', () => this.authenticationLogin());
    // this.addEventListener('click', this);
    // this.addEventListener('focus', this);

    // registerBtn.addEventListener(
    //   "click", function (e) {
    //     e.preventDefault();
    //     if(!e.target.classList.contains('activeBtn'))
    //     {
    //       // box.style.display = "none";
    //       registerBox.classList.remove("hidden");
    //       loginBox.classList.add("hidden");

    //       registerBtn.classList.add("activeBtn");
    //       loginBtn.classList.remove("activeBtn");
    //     }

    //   }
    // );



    // let validationRegex = [
    //   { regex: /.{8,}/ }, // min 8 letters,
    //   { regex: /[0-9]/ }, // numbers from 0 - 9
    //   { regex: /[a-z]/ }, // letters from a - z (lowercase)
    //   // { regex: /[A-Z]/}, // letters from A-Z (uppercase),
    //   // { regex: /[^A-Za-z0-9]/} // special characters
    // ]


    // this.password.addEventListener('keydown', this)

    this.addEventListener('keydown', this);


  }


  handleEvent(event) {
    this[`on${event.type}`](event)

  }

  onsubmit(e) {
    e.preventDefault();
    this.getData(e);
    this.postDats(e);
  }
  onkeydown(e) {
    if (e.target.id !== "password") {
      console.log("not password", e.target.id);
      return;
    }
    console.log("key down", e.target.id);
    let regex = /^(?=.*[a-z])(?=.*\d).{8,15}$/;
    console.log("password", e.target.value);
    if (regex.test(e.target.value)) {
      this.lengthPassword.style.color = "green";
      this.isValidPassword = true;
    }
    else
      this.lengthPassword.style.color = "red";

  }

  onclick(e) {

    // if (e.target.id === "intra")
    //   this.authenticationLogin();
    // else 
    if (e.target.id === "password" || e.target.id === 'confirm-password')
      this.lengthPassword.classList.remove("d-none");
    else
      this.lengthPassword.classList.add("d-none");
  }

  getData(event) {
    hideToast();
    if (!(event.target.id === "login-form")) return;

    showOverlay();
    this.email = this.querySelector("[data-email]");
    this.password = this.querySelector("[data-password]");
    this.user = {
      'email': this.email.value,
      'password': this.password.value,
    }
    const url = `http://localhost:8000/api/auth/login/`
    fetch(url, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-type': 'application/json',
      },
      credentials: "include",
      body: JSON.stringify(this.user),
    }).then(rep => rep.json())
      .then(data => {
        console.log(data);
        if (data.success) {
          hideOverlay();
          if (data.data.user.profile.is_tfa_enabled)
            navigateTo("/twofa");
          else
            navigateTo("/home");
        } else {
          showToast(true, data.message, data.errors);
          hideOverlay();
        }
      })
      .catch(_ => {
        showToast(true);
      });
  }

  postDats(event) {
    hideToast();

    if (!(event.target.id === "register-form")) return;


    this.firstName = this.querySelector("#firstName");
    this.lastName = this.querySelector("#lastName");
    this.password = this.querySelector("#password");
    this.confirmpassword = this.querySelector("#confirm-password");
    this.email = this.querySelector("#email");
    this.username = this.querySelector("#username");

    this.user = {
      'first_name': this.firstName.value,
      'last_name': this.lastName.value,
      'username': this.username.value,
      'email': this.email.value,
      'password': this.password.value,
      'confirm_password': this.confirmpassword.value,
    }

    const url = `http://localhost:8000/api/auth/register/`
    if (this.password.value !== this.confirmPassword.value || !this.isValidPassword) {
      console.log("passwords do not match");
      showToast("register-errors", "passwords do not match or password is not valid");
      this.password.value = "";
      this.confirmPassword.value = "";
      return;
    }
    fetch(url, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-type': 'application/json',
      },
      credentials: "include",
      body: JSON.stringify(this.user),
    }).then(rep => rep.json())
      .then(data => {
        if (data.success) {
          navigateTo("/login");
          showToast(false, data.message);
        }
        else
          showToast(true, data.message, data.errors);
      })
      .catch(_ => showToast(true));
  }

  async authenticationLogin() {
    showOverlay();
    const url = `http://localhost:8000/api/auth/intra/`
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          'Accept': 'application/json',
          'Content-type': 'application/json',
        },
        credentials: "include",
      });
      const data = await response.json();
      if (data.success) {
        hideOverlay();
        window.location.replace(data.data.url);
      } else {
        hideOverlay();
      }
    } catch (error) {
      hideOverlay();
      console.log(error);
    }

  }

  switcher(btn, btn2, box, box1) {
    btn.addEventListener(
      "click", function (e) {
        e.preventDefault();
        if (!e.target.classList.contains('activeBtn')) {
          box.classList.remove("hidden");
          box1.classList.add("hidden");
          btn.classList.add("activeBtn");
          btn2.classList.remove("activeBtn");
        }

      }
    );
  }

}



customElements.define("login-page", LoginPage);

export { LoginPage };
