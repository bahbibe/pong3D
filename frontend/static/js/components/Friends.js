import { API } from "../API/API.js";
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
    });
  }

  render() {
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
    friendElement.className = "friends-item p-2 mb-2 d-flex";
    friendElement.innerHTML = `
          <div class="col-12 col-md-2">
          <img src="${item.friend.profile.avatar}" class="img-fluid rounded-circle " width="100" alt="avatar"/>
          </div>
          <div class="conv d-none d-md-block">
          <h5>${item.friend.username}</h5>
          <p>last one </p>
          </div>
    `;
    friendElement.addEventListener("click", () => {
      const chatBox = document.querySelector(".chat-box");
      chatBox.innerHTML = "";
      chatBox.appendChild(new ChatBox(item));
    });
    return friendElement;
  }
}

window.customElements.define("friends-list", Friends);

export { Friends };
