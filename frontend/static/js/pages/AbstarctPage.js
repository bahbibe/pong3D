import WebSock from "../ws/ws.js";
import Notification from "../components/Notification.js";

class AbstractPage extends HTMLElement {
  constructor() {
    super();
    this.ws = new WebSock("notify");
  }

  get params() {
    return JSON.parse(this.getAttribute("params"));
  }

  async notify() {
    try {
      const message = await this.ws.receive();
      this.querySelector(".notification-container").appendChild(
        new Notification(message)
      );
      await this.notify();
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  }
}

export { AbstractPage };
