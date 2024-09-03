import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";


function switcher(btn, btn2, box, box1)
{
  btn.addEventListener(
    "click", function(e){
      e.preventDefault();
      if(!e.target.classList.contains('active'))
        {
          box.classList.remove("hidden");
          box1.classList.add("hidden");
        btn.classList.add("active");
        btn2.classList.remove("active");
      }
      
    }
  );
}

class LoginPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("login-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    
    const logninBtn = this.querySelector("[data-login]");
    this.loginForm = this.querySelector("#login-form");
    this.registerForm = this.querySelector("#register-form");
    this.intra = this.querySelector("#intra");
    
    
    // console.log(form);
    this.loginForm.addEventListener('submit',this);
    this.registerForm.addEventListener('submit',this);
    this.intra.addEventListener('click',this);

    const registerBtn = this.querySelector("#tab-register");
    const loginBtn = this.querySelector("#tab-login");
    const boxLogin = this.querySelector("#login");
    const boxRegister = this.querySelector("#register");
    switcher(registerBtn, loginBtn, boxRegister, boxLogin);
    switcher(loginBtn, registerBtn, boxLogin, boxRegister); 
    registerBtn.addEventListener(
      "click", function(e){
        e.preventDefault();
        if(!e.target.classList.contains('active'))
        {
          // box.style.display = "none";
          registerBox.classList.remove("hidden");
          loginBox.classList.add("hidden");
          
          registerBtn.classList.add("active");
          loginBtn.classList.remove("active");
        }
        
      }
    );
  }
  
  handleEvent(event) {
    this[`on${event.type}`](event)
  }

  onsubmit(e) {
    e.preventDefault();
    this.getData(e);
    this.postDats(e);
    // this.intraAutehnticate(e)
    
  }

  getData(event) {
    event.preventDefault();
    if(!(event.target.id === "login-form")) return;
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
        }
      })
      .catch(error => console.log("error"));
  }

  postDats(event) {
    event.preventDefault();
    if(!(event.target.id === "register-form")) return;
    console.log("register form", event.target.id);
        
    this.firstName = this.querySelector("#firstName");
    this.lastName = this.querySelector("#lastName");
    this.password = this.querySelector("#password");
    this.email = this.querySelector("#email");
    
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
      })
      .catch(error => console.log("error"));
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
        if (data.success)
        {
          // history.pushState(null, null, data.data.url);
          window.location.replace(data.data.url);
        }
      })
      .catch(error => console.log("error: ", error));
  }
}



customElements.define("login-page", LoginPage);

export { LoginPage };
