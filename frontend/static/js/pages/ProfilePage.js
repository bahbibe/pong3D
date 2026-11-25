import { escapeHTML as esc } from "../escape.js";
import { hideToast, showOverlay, hideOverlay, showToast, renderNotifications } from "../helpers.js";
import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";
import { API } from "../API/API.js";
import { BASE_URL } from "../router.js";
class ProfilePage extends AbstractPage {
  constructor() {
    super();
    this.API = new API();
  }

  connectedCallback() {
    const template = document.getElementById("user-profile");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    const ctn = this.querySelector(".profile-content");
    const fullName = this.querySelector("#fullName");
    const username = this.querySelector("#username");
    const userImg = this.querySelector("#user-img");
    const user = window.user;

    this.container = this.querySelector("#friend-container");
    this.blockedContainer = this.querySelector("#blocked-container");

    fullName.textContent = `${user.first_name} ${user.last_name}`;
    username.textContent = `@${user.username}`;
    userImg.src = `${user.profile.avatar}`;

    this.getFriend();
    this.getBlockedFriends();
    this.getStatGames();

    // Add event listener to container
    this.container.addEventListener("click", (e) => {
      const playButton = e.target.closest("[data-id]");
      if (playButton) {
        const friendId = playButton.dataset.id;
        this.API.invite_friend(friendId);
      }
    });
  }

  async getFriend() {
    try {
      showOverlay();
      const response = await fetch(`${BASE_URL}/api/friends/`, {
        credentials: "include",
      });
      const data = await response.json();
      if (response.ok) {
        const friends = data.data;
        for (const friend of friends) {
          let isOnline =
            window.online_users && window.online_users.includes(friend.friend.id.toString());
          this.container.innerHTML += `
              <div class="row p-1 rounded-1 justify-content-between align-items-center mb-2 glass-effect" style="cursor: pointer;" id="friend-${esc(friend.friend.id)}">
                <div class="col-3 col-md-4">
                  <div class="d-flex align-items-center">
                    <div class="position-relative">
                      <img src="${esc(friend.friend.profile.avatar)}" class="img-fluid rounded-circle" width="35" style="width: 35px; height: 35px;" alt="user profile image">
                      <div class="user-status ${isOnline ? "online" : ""}"></div>
                    </div>
                    <div class="ps-2">
                      <a href="friend/${esc(friend.friend.profile.uuid)}"><span class="fw-bold text-capitalize" style="font-size: 14px;">${esc(friend.friend.username)}</span></a>
                    </div>
                  </div>
                </div>
                <div class="col-2 pe-2 ">
                  <span id="total"><strong>100</strong></span>
                </div>
                <div class="col-2 pe-2 ">
                  <span id="wins"><strong>100</strong></span>
                </div>
                <div class="col-2 pe-2 d-none d-md-block">
                  <span id="ratio"><strong>100</strong></span>
                </div>
                <div class="col-3 col-md-2 text-end">
                  <a data-id="${esc(friend.friend.id)}" role="button" class="bg-success font-glitch text-white text-decoration-none p-1">PLAY</a>
                </div>
              </div>
          `;
        }
        hideOverlay();
      }
    } catch (e) {
      console.log(e);
    }
  }

  async getBlockedFriends() {
    try {
      const response = await fetch(`${BASE_URL}/api/friends/blocked/`, {
        credentials: "include",
      });
      const data = await response.json();
      const users = data.data;

      this.blockedContainer.innerHTML = "";

      for (const user of users) {
        this.blockedContainer.innerHTML += `
            <div class="row  p-1 rounded-1 justify-content-between align-items-center mb-2 glass-effect" style="cursor: pointer;">
                  <div class="col-6">
                    <div class="d-flex align-items-center">
                    <img src="${esc(user.friend.profile.avatar)}" class="img-fluid rounded-circle" width="35" style="width: 35px; height: 35px" alt="user profile image">
                      <div class="ps-2">
                        <span class="fw-bold text-capitalize" style="font-size: 14px;">${esc(user.friend.username)}</span>
                      </div>
                    </div>
                  </div>
                  <div class="col-4 text-end">
                    <button data-unblock="${esc(user.friend.id)}" role="button" class="btn btn-block bg-danger p-1">Unblock</button>
                  </div>
                </div>
            `;
      }
      this.unblockBtn = this.querySelectorAll("[data-unblock]");
      this.unblockBtn.forEach((btn) => {
        btn.addEventListener("click", this.unblockFriend.bind(this));
      });
    } catch (error) {
      console.log(error);
    }
  }

  async unblockFriend(e) {
    try {
      console.log(e.target.getAttribute("data-unblock"));
      const url = `${BASE_URL}/api/friends/unblock/`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: e.target.getAttribute("data-unblock"),
        }),
      });
      const data = await response.json();
      if (response.ok) this.getBlockedFriends();
    } catch (error) {
      console.log(error);
    }
  }
  async getStatGames() {
    try {
      const total = this.querySelector(".total");
      const wins = this.querySelector(".wins");
      const losses = this.querySelector(".losses");
      const ratio = this.querySelector(".ratio");
      const gamesContainer = this.querySelector("#games-container");

      const response = await fetch(`${BASE_URL}/api/game/history/`, {
        credentials: "include",
      });
      if (!response.ok) return;
      const data = await response.json();
      const stats = data.data.stats;
      // A game whose opponent account was deleted has no player to show.
      const games = data.data.games.filter((game) => game.user && game.player);

      if (response.ok) {
        total.textContent = `${stats.total_games} Matches`;
        wins.textContent = `${stats.total_wins} Wins`;
        losses.textContent = `${stats.total_losses} Losses`;
        ratio.textContent = `${stats.ratio}%`;

        for (const game of games) {
          gamesContainer.innerHTML += `
              <div class="row mt-3 p-1 mb-1 glass-effect">
                  <div class="col-4 my-auto p-0">
                    <div class="d-md-flex align-items-center">
                      <img src="${esc(game.user.profile.avatar)}" class="img-fluid rounded-circle d-none d-md-block"
                        width="40" style="width: 40px; height: 40px" alt="user profile image">
                      <div class="ps-2">
                        <span class="fw-bold text-capitalize">${esc(game.user.username)}</span>
                      </div>
                    </div>
                  </div>
                  <div class="col-2 col-md-2 my-auto text-center">
                    <span class="result fw-bolder ">${esc(game.user_score)}:${esc(game.player_score)}</span>
                  </div>
                  <div class="col-4 my-auto p-0 text-center">
                    <div class="d-md-flex justify-content-center align-items-center">
                      <div class="pe-2">
                        <span class="fw-bold text-capitalize">${esc(game.player.username)}</span>
                      </div>
                      <img src="${esc(game.player.profile.avatar)}" class="img-fluid rounded-circle d-none d-md-block"
                        width="40" style="width: 40px; height: 40px" alt="user profile image">
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
      console.log(error);
    }
  }
}

class mainNav extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("main-nav");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    const navUsername = this.querySelector("#nav-username");
    const navUserImg = this.querySelector("#nav-user-img");
    this.notification = this.querySelector(".notification-ui_dd-content");
    this.notificationCounter = this.querySelector("[data-count]");
    this.logoutBtn = this.querySelector("#logout");
    const user = window.user;
    navUsername.textContent = `${user.username}`;
    navUserImg.src = `${user.profile.avatar}`;

    // this.RequestFriends();
    this.notificationBtn = this.querySelector("#notification-btn");
    this.notificationBtn.addEventListener("click", () => {
      this.notification.innerHTML = `<p class="text-center my-2">No new notifications</p>`;
      this.notificationCounter.textContent = 0;
      this.notificationBtn.classList.add("disabled");
      window.notifications = [];
      this.markNotificationsAsRead();
    });
    renderNotifications();
    this.logoutBtn.addEventListener("click", this.logout);

    // this.notification.addEventListener("click", (e) => {
    //   const playButton = e.target.closest("[data-game]");
    //   if (playButton) {
    //     const game = playButton.dataset.game;
    //     navigateTo(`/play/${game}`);
    //   }
    // });
  }

  handleEvent(event) {
    this[`on${event.type}`](event);
  }

  // onclick(e) {
  //   e.preventDefault();
  //   if (e.target.id === "logout")
  //     this.logout();
  // }

  RequestFriends() {
    fetch(`${BASE_URL}/api/friends/requests/`, {
      method: "GET",
      credentials: "include",
    })
      .then((response) => response.json())
      .then((data) => {
        const friends = data.data;
        this.notificationCounter.textContent = friends.length;
        friends.forEach((element) => {
          console.log();
          this.notification.innerHTML += `
          <div class="notification">
                        <img src="${esc(element.friend.profile.avatar)}" alt="" />
                        <div class="text">
                            <p>
                                <a href="friend/${esc(element.friend.profile.uuid)}"><span class="name">${esc(element.friend.username)}</span> </a> has send a friend request
                            </p>
                        </div>
                    </div>
          `;
        });
      })
      .catch((error) => {
        console.log(error);
      });
  }

  async markNotificationsAsRead() {
    try {
      fetch(`${BASE_URL}/api/auth/notifications/mark_as_read/`, {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.log(error);
    }
  }

  async logout(e) {
    // The link is href="#": following it fires popstate, and the router
    // would render the page again while the logout request is running.
    if (e) e.preventDefault();
    try {
      const url = `${BASE_URL}/api/auth/logout/`;
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
      });
      const data = await response.json();
      if (response.status === 200) {
        if (window.socket) {
          window.socket.close();
        }
        if (window.notif_socket) {
          window.notif_socket.close();
        }
        window.user = null;
        navigateTo("/login");
      }
    } catch (e) {
      console.log(e);
    }
  }
}

window.customElements.define("user-profile", ProfilePage);
window.customElements.define("main-nav", mainNav);

export { ProfilePage };
