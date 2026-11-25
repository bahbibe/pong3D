export class ErrorToast extends HTMLElement {
  constructor(message) {
    super();
    this.message = message;
  }
  connectedCallback() {
    const template = document.getElementById("error-toast");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
  }

  async render() {
    this.querySelector(".toast-body").textContent = this.message ?? "";
  }
}
