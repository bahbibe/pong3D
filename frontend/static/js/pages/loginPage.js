class Login extends HTMLElement {
    constructor() {
      super()
    }
  
    connectedCallback() {
      const template = document.getElementById("login-page");
      const clone = template.content.cloneNode(true);
      this.appendChild(clone);
  
    }
  }
  
  window.customElements.define("login-page", Login);
  
  export { Login }