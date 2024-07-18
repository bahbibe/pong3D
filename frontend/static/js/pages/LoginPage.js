import { AbstractPage } from "./AbstarctPage.js";

class LoginPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("login-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const registerBtn = this.querySelector("#tab-register");
    const loginBtn = this.querySelector("#tab-login");
    const boxLogin = this.querySelector("#login");
    const boxRegister = this.querySelector("#register");
    switcher(registerBtn, loginBtn, boxRegister, boxLogin);
    switcher(loginBtn, registerBtn, boxLogin, boxRegister); 
    // registerBtn.addEventListener(
    //   "click", function(e){
    //     e.preventDefault();
    //     if(!e.target.classList.contains('active'))
    //     {
    //       // box.style.display = "none";
    //       registerBox.classList.remove("hidden");
    //       loginBox.classList.add("hidden");
          
    //       registerBtn.classList.add("active");
    //       loginBtn.classList.remove("active");
    //     }
        
    //   }
    // );

    // loginBtn.addEventListener(
    //   "click", function(e){
    //     e.preventDefault();
    //     if(!e.target.classList.contains('active'))
    //     {
    //       box.style.display = "block";
    //       loginBtn.classList.add("active");
    //       registerBtn.classList.remove("active");
    //     }
        
    //   }
    // );


  //   this.querySelector("#login-form").addEventListener(
  //     "submit",
  //     this.handleSubmit
  //   );
  // }
  // async handleSubmit(e) {
  //   e.preventDefault();
  //   try {
  //     const username = e.target.querySelector("#username").value;
  //     const password = e.target.querySelector("#password").value;
  //     const response = await fetch("http://localhost:8000/api/auth/login/", {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({ username, password }),
  //       credentials: "include",
  //     });
  //     e.target.reset();
  //     if (!response.ok) {
  //       throw new Error(`Login failed : ${response.status}`);
  //     }
  //   } catch (error) {
  //     alert(`${error.message}`);
  //   }
  }
}


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
          console.log(box1);
        btn.classList.add("active");
        btn2.classList.remove("active");
      }
      
    }
  );
}



customElements.define("login-page", LoginPage);

export { LoginPage };
