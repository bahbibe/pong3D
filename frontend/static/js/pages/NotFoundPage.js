class NotFoundPage extends HTMLElement {
  constructor() {
    super()
  }

  connectedCallback() {
    const template = document.getElementById("not-found-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
  }
}

window.customElements.define("not-found-page", NotFoundPage);

export { NotFoundPage }
