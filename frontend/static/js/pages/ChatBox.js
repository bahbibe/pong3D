import API from "../API/API.js";

class ChatBox extends HTMLElement {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.API = new API();
    this.render();
    // this.querySelector(".close").addEventListener("click", this.closeChatbox);
  }
  async render() {
    try {
      const uuid = this.API.getUser().uuid;
      this.messages = await this.API.getMessages(uuid);
      const messagesList = this.querySelector("#chat-messages");
      messagesList.innerHTML = "";
      if (this.messages.length === 0) {
        const noMessages = document.createElement("p");
        noMessages.innerText = "No messages found";
        messagesList.appendChild(noMessages);
      }

      console.log(this.messages);
      // for (const message of this.messages) {
      //   const messageElement = document.createElement("div");
      //   messageElement.setAttribute("class", "message");
      //   messageElement.innerHTML = `
      //       <li>
      //         <img class="avatar" src="${message.author.profile.avatar}" alt="avatar"/>  
      //         <span>${message.author.username}</span>
      //         <p>${message.content}</p>
      //       </li>
      //   `;
      //   this.querySelector("#messages").appendChild(messageElement);
      // }
    } catch (error) {
      console.error("Error rendering messages:", error);
    }
  }
  // closeChatbox() {
  //   this.parentNode.removeChild(this);
  // }
}

customElements.define("chat-box", ChatBox);

export default ChatBox;