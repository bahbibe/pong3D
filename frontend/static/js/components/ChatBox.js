import API from "../API/API.js";
import WebSock from "../ws/ws.js";

class ChatBox extends HTMLElement {
  constructor(uuid) {
    super();
    this.API = new API();
    this.uuid = uuid;
    // this.WebSock = null;
  }
  connectedCallback() {
    // const template = document.getElementById("chat");
    // const clone = template.content.cloneNode(true);
    // this.appendChild(clone);
    this.render();
    // this.WebSock = new WebSock(this.uuid);
    // this.WebSock.connect();
    // this.receiveMessage();
    // this.querySelector("#chat-form").addEventListener("submit", (event) => {
    //   event.preventDefault();
    //   this.sendMessage(event);
    // });
  }
  // async receiveMessage() {
  //   try {
  //     const message = await this.WebSock.receive();
  //     if (!message) {
  //       return;
  //     }
  //     this.querySelector("#chat-messages").appendChild(
  //       this.createMessageElement(JSON.parse(message))
  //     );
  //     await this.receiveMessage();
  //   } catch (error) {
  //     console.error("Error receiving message:", error);
  //   }
  // }

  // disconnectedCallback() {
  //   if (this.WebSock) {
  //     this.WebSock.close();
  //   }
  // }

  async render() {
    try {
      this.messages = await this.API.getMessages(this.uuid);
      this.messages.forEach((item) => {
        this.appendChild(this.createMessageElement(item));
      });
      if (this.messages.length === 0) {
        this.appendChild(document.createTextNode("No messages yet"));
      } 
    } catch (error) {
      console.error("Error rendering chat list:", error);
      this.appendChild(document.createTextNode("Error loading messages"));
    }
  }

  createMessageElement(item) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message-box");
    messageElement.innerHTML = `
      <div class="message-item">
        <span>${item.content}</span>
        <span>${new Date(item.timestamp).toLocaleString()}</span>
      </div>
    `;
    return messageElement;
  }

  // async sendMessage(event) {
  //   const message = event.target.querySelector("#chat-input").value;
  //   if (message) {
  //     try {
  //       await this.WebSock.send({
  //         content: message,
  //         timestamp: new Date(), //.toLocaltring(), if needed
  //         conversation: this.uuid,
  //       });
  //       event.target.reset();
  //     } catch (error) {
  //       console.error("Error sending message:", error);
  //     }
  //   }
  // }
}

window.customElements.define("chat-box", ChatBox);

export { ChatBox };
