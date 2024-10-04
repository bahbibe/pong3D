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

    this.fullName = this.querySelector("#fullName");
    this.username = this.querySelector("#username");
    this.userImg = this.querySelector("#user-img");
    this.addFriend = this.querySelector("#add-friend");
    this.isSent = false;
    
    this.getUser();
    this.CheckIsFriend();
    if (!this.isSent)
        this.checkIsSent();
    if (!this.isSent)
      this.checkIsSend();

    this.addFriend.addEventListener("click", this);

  }
  handleEvent(e) {
    this[`on${e.type}`](e);
  }
  onclick(e) {
    if (this.addFriend.getAttribute("data-accept")) {
      this.acceptRequest();
    } else {
      this.sendRequest();
    }
  }

  async getUser() {
    try {
      const response = await fetch(`http://localhost:8000/api/auth/user/${this.userId.id}`, {
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
        const user = res.data;
        this.fullName.textContent = `${user.first_name} ${user.last_name}`;
        this.username.textContent = `@${user.username}`;
        this.userImg.src = `${user.profile.avatar}`;
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
        body: JSON.stringify({ target_user: this.userId.id }),
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
      const response = await fetch(`http://localhost:8000/api/friends/update/`, {
        method: "PUT",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ friend_id: this.userId.id , status: "accepted"}),
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
        if (friend.friend.id === +this.userId.id) {
            // navigateTo(`/friend${this.userId.id}`);
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-check me-2"></i> friends`;
            this.addFriend.disabled = true;
            window.isSent = true;
            break;
        }
    }
  }


  async checkIsSent() {
    console.log("checkIsSent");
    const response = await fetch("http://localhost:8000/api/friends/sent", {
      method: "GET",
      credentials: "include",
    });
    const data = await response.json();
    for (const friend of data.data) {
      console.log(friend.friend.id , +this.userId.id);
        if (friend.friend.id === +this.userId.id) {
            this.isSent = true;
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-clock me-2"></i> pending`;
            this.addFriend.disabled = true;
            break;
        }
    }
  }

  async checkIsSend() {
    console.log("checkIsSend", window.isSent);
    const response = await fetch("http://localhost:8000/api/friends/requests/", {
      method: "GET",
      credentials: "include",
    });
    const data = await response.json();
    const  rqts = data.data
    for (const rqt of rqts) {
      console.log(rqt.friend.id , +this.userId.id);
        if (rqt.friend.id === +this.userId.id) {
            this.addFriend.innerHTML = `<i class="fa-solid fa-user-plus fa-sm me-2"></i> accept`;
            this.addFriend.setAttribute("data-accept", true);
            break;
        }
    }
  }
}


window.customElements.define("friend-page", FriendPage);


export { FriendPage }