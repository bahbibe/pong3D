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
          // console.log(box);
          // console.log(box1);
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
    this.form = this.querySelector("form");
    
    
    // console.log(form);
    this.form.addEventListener('submit',this);

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

    const url = `http://127.0.0.1:8000/api/auth/register/`
    fetch(url, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: "include",
      body: JSON.stringify(this.user),
    }).then(rep => rep.json())
      .then(data => {
        console.log(data);
        if (data.success)
        {
          console.log(`good`);
          history.pushState(null, null, `http://127.0.0.1:3000/home`);
          history.replaceState(null, null, `http://127.0.0.1:3000/home`);
          location.reload();
        }
      })
      .catch(error => console.log("error"));
    
  }


}




customElements.define("login-page", LoginPage);

export { LoginPage };
