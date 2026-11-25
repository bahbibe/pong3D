import { showOverlay, hideOverlay } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";
import { BASE_URL } from "../router.js";
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

    this.blockFriend = this.querySelector("#block");

    this.isSent = false;

    showOverlay();
    this.getUser();
    this.CheckIsFriend();

    if (!this.isSent) {
      this.checkIsSent();
      hideOverlay();
    }
    if (!this.isSent) {
      this.checkIsSend();
      hideOverlay();
    }

    this.addFriend.addEventListener("click", this);
    this.blockFriend.addEventListener("click", () => this.blockingFriend());
  }

  handleEvent(e) {
    this[`on${e.type}`](e);
  }

  onclick() {
    if (this.addFriend.getAttribute("data-accept")) {
      this.acceptRequest();
    } else {
      this.sendRequest();
    }
  }

  async getUser() {
    try {
      const response = await fetch(`${BASE_URL}/api/auth/profile/${this.userId.uuid}/`, {
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
      } else {
        const total = this.querySelector(".total");
        const wins = this.querySelector(".wins");
        const losses = this.querySelector(".losses");
        const ratio = this.querySelector(".ratio");
        const friendHistory = this.querySelector("#friend-history");

        this.friend = res.data.user;
        const stats = res.data.stats;
        const games = res.data.history;

        this.fullName.textContent = `${this.friend.first_name} ${this.friend.last_name}`;
        this.username.textContent = `@${this.friend.username}`;
        this.userImg.src = `${this.friend.profile.avatar}`;

        total.textContent = `${stats.total_games} Matches`;
        wins.textContent = `${stats.total_wins} Wins`;
        losses.textContent = `${stats.total_losses} Losses`;
        ratio.textContent = `${stats.ratio}%`;

        for (const game of games) {
          friendHistory.innerHTML += `
              <div class="row mt-3 p-1 mb-1 glass-effect">
                  <div class="col-4 my-auto p-0">
                    <div class="d-md-flex align-items-center">
                      <img src="${
                        game.user.profile.avatar
                      }" class="img-fluid rounded-circle d-none d-md-block"
                       style="width: 40px; height: 40px" alt="user profile image">
                      <div class="ps-2">
                        <span class="fw-bold text-capitalize">${game.user.username}</span>
                      </div>
                    </div>
                  </div>
                  <div class="col-2 col-md-2 my-auto text-center">
                    <span class="result fw-bolder ">${game.user_score}:${game.player_score}</span>
                  </div>
                  <div class="col-4 my-auto p-0 text-center">
                    <div class="d-md-flex justify-content-center align-items-center">
                      <div class="pe-2">
                        <span class="fw-bold text-capitalize">${game.player.username}</span>
                      </div>
                      <img src="${
                        game.player.profile.avatar
                      }" class="img-fluid rounded-circle d-none d-md-block"
                        style="width: 40px; height: 40px" alt="user profile image">
                    </div>
                  </div>
                  <div class="col-2 my-auto text-center" style="cursor:pointer;">
                    <span class="result h3" aria-label="${
                      game.is_user_winner ? "WIN" : "LOSE"
                    }">${game.is_user_winner ? "🏆" : "😓"}</span>
                  </div>
              </div>
          `;
        }
      }
    } catch (error) {
      console.error("Error Loading profile:", error);
    }
  }

  async sendRequest() {
    try {
      const response = await fetch(`${BASE_URL}/api/friends/send/`, {
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
      const response = await fetch(`${BASE_URL}/api/friends/accept/`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ source_user: this.friend.id }),
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
    const response = await fetch(`${BASE_URL}/api/friends/`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) return; // e.g. logged out meanwhile
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
    const response = await fetch(`${BASE_URL}/api/friends/sent-requests/`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) return; // e.g. logged out meanwhile
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
    const response = await fetch(`${BASE_URL}/api/friends/requests/`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) return; // e.g. logged out meanwhile
    const data = await response.json();
    const rqts = data.data;
    for (const rqt of rqts) {
      if (rqt.friend.profile.uuid === this.userId.uuid) {
        this.addFriend.innerHTML = `<i class="fa-solid fa-user-plus fa-sm me-2"></i> accept`;
        this.addFriend.setAttribute("data-accept", true);
        break;
      }
    }
  }

  async blockingFriend() {
    try {
      const response = await fetch(`${BASE_URL}/api/friends/block/`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ user_id: this.friend.id }),
      });

      if (response.ok) {
        navigateTo("/home");
      }
    } catch (error) {
      console.error("Error Blocking Request:", error);
    }
  }
}

window.customElements.define("friend-page", FriendPage);

export { FriendPage };
