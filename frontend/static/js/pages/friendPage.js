import { showOverlay, hideOverlay } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class FriendPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("friend-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.userId = JSON.parse(this.getAttribute("params"));
    // console.log("UUID: " , this.userId.uuid);

    this.fullName = this.querySelector("#fullName");
    this.username = this.querySelector("#username");
    this.userImg = this.querySelector("#user-img");
    this.addFriend = this.querySelector("#add-friend");

    this.blockFriend = this.querySelector("#block");

    this.isSent = false;

    
    showOverlay();
    this.getUser();
    this.CheckIsFriend();

    if (!this.isSent)
    {
      this.checkIsSent();
      hideOverlay();
    }
    if (!this.isSent)
    {
      this.checkIsSend();
      hideOverlay();
    }

    this.addFriend.addEventListener("click", this);
    this.blockFriend.addEventListener("click", () => this.blockingFriend());

  }

  handleEvent(e) {
    this[`on${e.type}`](e);
  }

  onclick(e) {
    if (this.addFriend.getAttribute("data-accept")) {
      this.acceptRequest();
    }
    else {
      this.sendRequest();
    }
  }

  async getUser() {
    try {
      const response = await fetch(`http://localhost:8000/api/auth/profile/${this.userId.uuid}/`, {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });

      const res = await response.json();
      if (!response.ok) {
        if (response.status === 404) {
          navigateTo("/home");
        }
        throw new Error(res.error);
      }
      else
      {
        this.friend = res.data;
        this.fullName.textContent = `${this.friend.first_name} ${this.friend.last_name}`;
        this.username.textContent = `@${this.friend.username}`;
        this.userImg.src = `${this.friend.profile.avatar}`;
      }
    } catch (error) {
      console.error("Error Loading profile:", error);
    }
  }

  async sendRequest() {
    try {
      const response = await fetch(`http://localhost:8000/api/friends/send/`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ target_user: this.friend.id }),
      });

      if (response.ok) {
        this.addFriend.innerHTML = `<i class="fa-solid fa-user-clock me-2"></i> pending`;
        this.addFriend.disabled = true;
        window.isSent = true;
      }
    } catch (error) {
      console.error("Error Sending Request:", error);
    }
  }
  
  async acceptRequest() {
    try {
      const response = await fetch(`http://localhost:8000/api/friends/accept/`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ source_user: this.friend.id}),
      });

      if (response.ok) {
        this.addFriend.innerHTML = `<i class="fa-solid fa-user-check me-2"></i> friends`;
        this.addFriend.disabled = true;
        window.isSent = true;
      }
    } catch (error) {
      console.error("Error Accepting Request:", error);
    }
  }

  async CheckIsFriend() {
    const response = await fetch("http://localhost:8000/api/friends/", {
      method: "GET",
      credentials: "include",
    });
    const data = await response.json();
    for (const friend of data.data) {
        if (friend.friend.profile.uuid === this.userId.uuid) {
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-check me-2"></i> friends`;
            this.addFriend.disabled = true;
            window.isSent = true;
            break;
          }
    }  
  }

  async checkIsSent() {
    const response = await fetch("http://localhost:8000/api/friends/sent-requests/", {
      method: "GET",
      credentials: "include",
    });
    const data = await response.json();
    for (const friend of data.data) {
        if (friend.friend.profile.uuid === this.userId.uuid) {
            this.isSent = true;
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-clock me-2"></i> pending`;
            this.addFriend.disabled = true;
            break;
        }
    }
  }

  async checkIsSend() {
    const response = await fetch("http://localhost:8000/api/friends/requests/", {
      method: "GET",
      credentials: "include",
    });
    const data = await response.json();
    const  rqts = data.data
    for (const rqt of rqts) {
        if (rqt.friend.profile.uuid === this.userId.uuid) {
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-plus fa-sm me-2"></i> accept`;
            this.addFriend.setAttribute("data-accept", true);
            break;
        }
    }
  }

  async blockingFriend() {
    console.log("start blocking");
    try {
      const response = await fetch(`http://localhost:8000/api/friends/block/`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ user_id: this.friend.id}),
      });

      if (response.ok) {
        console.log("Blocked");
        navigateTo("/home");
      }
    } catch (error) {
      console.error("Error Blocking Request:", error);
    }
  }
}


window.customElements.define("friend-page", FriendPage);


export { FriendPage }