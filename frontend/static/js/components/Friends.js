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
    friendElement.className = "contact  p-2 m-2 mb-3 d-flex gap-2";
    friendElement.innerHTML = `
          <div class="col-12 col-md-3 col-lg-2 d-flex justify-content-center align-items-center">
          <img src="${item.friend.profile.avatar}" class="img-fluid rounded-circle h-md-75 h-sm-100" alt="avatar"/>
          </div>
          <div class="d-none d-md-block col-md-9 col-lg-10">
          <div class="last-msg d-flex flex-column h-100 justify-content-center">
          <p class="m-0 fs-5">${item.friend.username}</p>
          <p class="m-0 opacity-75">a AKJsygfdjkghLAKSJDHJGASKFGAKJHSDGFAGSDFHJGASDHJFG </p>
          </div>
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
