import { escapeHTML as esc } from "../escape.js";
import { API } from "../API/API.js";
import { ChatBox } from "../components/ChatBox.js";

class Friends extends HTMLElement {
  constructor() {
    super();
    this.API = new API();
    this.friends = [];
    this.activeElement = null;
  }

  connectedCallback() {
    this.addEventListener("click", this.FriendClick);
    this.API.getFriends().then((res) => {
      this.friends = res;
      this.render();
    });
  }

  FriendClick = (event) => {
    const clickedFriend = event.target.closest(".contact");
    if (clickedFriend) {
      if (this.activeElement) {
        this.activeElement.classList.remove("active");
      }
      clickedFriend.classList.add("active");
      this.activeElement = clickedFriend;
      const friendItem = this.friends.find((item) => {
        return item.friend.username === clickedFriend.querySelector("p").textContent;
      });
      const chatBox = document.querySelector(".chat-box");
      chatBox.innerHTML = "";
      chatBox.appendChild(new ChatBox(friendItem));
    }
  };

  render() {
    this.innerHTML = "";
    this.documentElement = document.createElement("div");
    this.documentElement.className = "friends-list no-scroll p-2 blur";
    try {
      this.friends.forEach((item) => {
        const friendElement = this.FriendElement(item);
        this.appendChild(friendElement);
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
    friendElement.className = "contact p-2 mx-1 d-flex gap-2";
    friendElement.innerHTML = `
      <div class="d-flex align-items-center">
          <img src="${esc(item.friend.profile.avatar)}" class="d-block img-cover img-fluid rounded-circle" alt="avatar"/>
      </div>
      <div class="d-none d-md-block col-md-9 col-lg-10">
        <div class="last-msg d-flex flex-column h-100 justify-content-center">
          <p class="m-0 fs-5">${esc(item.friend.username)}</p>
          <p class="m-0 opacity-75">lore ipsum</p>
        </div>
      </div>
    `;
    return friendElement;
  }
}

window.customElements.define("friends-list", Friends);

export { Friends };
