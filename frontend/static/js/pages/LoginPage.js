import { AbstractPage } from "./AbstarctPage.js";

class LoginPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("login-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.querySelector("#login-form").addEventListener(
      "submit",
      this.handleSubmit
    );
  }
  async handleSubmit(e) {
    e.preventDefault();
    try {
      const username = e.target.querySelector("#username").value;
      const password = e.target.querySelector("#password").value;
      const response = await fetch("http://localhost:8000/api/auth/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      });
      e.target.reset();
      if (!response.ok) {
        throw new Error(`Login failed : ${response.status}`);
      }
    } catch (error) {
      alert(`${error.message}`);
    }
  }
}
customElements.define("login-page", LoginPage);

export { LoginPage };
