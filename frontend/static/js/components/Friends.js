import API from "../API/API.js";
import { ChatBox } from "./ChatBox.js";

class Friends extends HTMLElement {
  constructor() {
    super();
    this.API = new API();
    this.friends = [];
  }
  connectedCallback() {
    this.API.getFriends().then((res) => {
      this.friends = res;
      this.render();
    }
    );
  }
  
  async render() {
    try {
      this.friends.forEach((item) => {
        this.appendChild(this.FriendElement(item));
      });
      if (this.friends.length === 0) {
        this.appendChild(document.createTextNode("No friends yet"));
      }
    } catch (error) {
      console.error("Error rendering friends list:", error);
      this.appendChild(document.createTextNode("Error loading friends list"));
    }
  }
  FriendElement(item) {
    const friendElement = document.createElement("div");
    friendElement.classList.add("friends-item");
    friendElement.innerHTML = `
          <div class="avatar">
          <img src="${item.friend.profile.avatar}" alt="avatar"/>
          </div>
          <div class="message">
          <h5>${item.friend.username}</h5>
          <p> lorem ipsum dolor sit amet, consectetur adipiscing elit.
          lorem ipsum dolor sit amet, consectetur adipiscing elit. </p>
          <span class="time"> 13:37 </span>
          </div>
    `;
    friendElement.addEventListener("click", () => {
      const chatBox = document.querySelector(".chat-box");
      chatBox.innerHTML = `
      <div class="chat-box">
        <img class="loading" src="/static/img/loading.gif" alt="loading"/>
        <chat-box></chat-box>
      </div>
      `;
      
      // new ChatBox(item.friend.profile.uuid);
    });
    return friendElement;
  }
}

window.customElements.define("friends-list", Friends);

export { Friends };
