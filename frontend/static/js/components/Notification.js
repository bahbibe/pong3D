class Notification extends HTMLElement {
  constructor(message) {
    super();
    this.message = message;
  }
  connectedCallback() {
    const template = document.getElementById("notification");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
    this.querySelector("#close-notification").addEventListener("click", () => {
      this.parentNode.removeChild(this);
    });
  }
  async render() {
    try {
      this.querySelector("#notification-message").textContent = this.message ?? "";
      setTimeout(() => {
        this.parentNode.removeChild(this);
      }, 5000);
    } catch (error) {
      console.error("Error rendering notifications:", error);
    }
  }
}

customElements.define("notification-item", Notification);

export default Notification;
