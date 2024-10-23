import { hideToast, showToast } from "../helpers.js";
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
    this.email = this.querySelector("#email");

    this.lengthPassword = this.querySelector(".lengthPassword");
    const logninBtn = this.querySelector("[data-login]");
    this.loginForm = this.querySelector("#login-form");
    this.registerForm = this.querySelector("#register-form");
    this.intra = this.querySelector("#intra");

    // console.log(form);
    this.loginForm.addEventListener('submit', this);
    this.registerForm.addEventListener('submit', this);
    this.intra.addEventListener('click', this);

    const registerBtn = this.querySelector("#tab-register");
    const loginBtn = this.querySelector("#tab-login");
    const boxLogin = this.querySelector("#login");
    const boxRegister = this.querySelector("#register");

    this.switcher(registerBtn, loginBtn, boxRegister, boxLogin);
    this.switcher(loginBtn, registerBtn, boxLogin, boxRegister);
    registerBtn.addEventListener(
      "click", function (e) {
        e.preventDefault();
        if(!e.target.classList.contains('activeBtn'))
        {
          // box.style.display = "none";
          registerBox.classList.remove("hidden");
          loginBox.classList.add("hidden");
          
          registerBtn.classList.add("activeBtn");
          loginBtn.classList.remove("activeBtn");
        }

      }
    );



let validationRegex = [
  { regex: /.{8,}/ }, // min 8 letters,
  { regex: /[0-9]/ }, // numbers from 0 - 9
  { regex: /[a-z]/ }, // letters from a - z (lowercase)
  { regex: /[A-Z]/}, // letters from A-Z (uppercase),
  { regex: /[^A-Za-z0-9]/} // special characters
]

this.password.addEventListener('keydown', () => {
  let count = 0;
  validationRegex.forEach((item, i) => {
    console.log(password.value);
    let isValid = item.regex.test(password.value);
    if(isValid)
    {
      count++;
      console.log("count", count);
    }
    if(count === 5)
      this.lengthPassword.style.color = "green";
    else
      this.lengthPassword.style.color = "red";
  })
});


}


  handleEvent(event) {
    this[`on${event.type}`](event)
  }

  onsubmit(e) {
    e.preventDefault();
    this.getData(e);
    this.postDats(e);
  }
  // onkeydown(e) { 
  //   this.isValidPassword(e.key);
  // }

  getData(event) {
    hideToast("login-errors");
    if (!(event.target.id === "login-form")) return;

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
          navigateTo("/home");
        } else {
          showToast("login-errors", data.message, data.errors);
        }
      })
      .catch(_ => {
        showToast("login-errors");
      });
  }

  postDats(event) {
    hideToast("register-errors");

    if (!(event.target.id === "register-form")) return;

    console.log("register form", event.target.id);


    this.user = {
      'first_name': this.firstName.value,
      'last_name': this.lastName.value,
      'username': this.firstName.value[0] + this.lastName.value,
      'email': this.email.value,
      'password': this.password.value,
    }

    const url = `http://localhost:8000/api/auth/register/`
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
        if (data.success)
          navigateTo("/login");
        else
          showToast("register-errors", data.message, data.errors);
      })
      .catch(_ => showToast("register-errors"));
  }
  onclick(e) {
    e.preventDefault();

    const url = `http://localhost:8000/api/auth/intra/`
    fetch(url, {
      method: "GET",
      headers: {
        'Accept': 'application/json',
        'Content-type': 'application/json',
      },
      credentials: "include",
    }).then(rep => rep.json())
      .then(data => {
        if (data.success) {
          // history.pushState(null, null, data.data.url);
          window.location.replace(data.data.url);
        }
      })
      .catch(_ => showToast("login-errors"));
  }

  switcher(btn, btn2, box, box1) {
    btn.addEventListener(
      "click", function (e) {
        e.preventDefault();
        if(!e.target.classList.contains('activeBtn'))
          {
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
