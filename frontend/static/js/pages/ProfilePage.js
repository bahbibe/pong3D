import { escapeHTML as esc } from "../escape.js";
import { showOverlay, hideOverlay } from "../helpers.js";
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

  // Games, wins and ratio of every player, and their rank (the leaderboard is
  // sorted). Map of user id to {total_games, total_wins, ratio, rank}.
  async loadLeaderboard() {
    const response = await fetch(`${BASE_URL}/api/game/leaderboard/`, { credentials: "include" });
    if (!response.ok) return new Map();
    const body = await response.json();
    return new Map(body.data.users.map((row, index) => [row.user.id, { ...row, rank: index + 1 }]));
  }

  async getFriend() {
    showOverlay();
    try {
      const [response, board] = await Promise.all([
        fetch(`${BASE_URL}/api/friends/`, { credentials: "include" }),
        this.loadLeaderboard(),
      ]);
      const myRank = board.get(window.user.id)?.rank;
      this.querySelector("#profile-rank").textContent = myRank ? `#${myRank}` : "-";
      const data = await response.json();
      if (!response.ok) return;
      this.container.innerHTML = data.data
        .map((friend) => {
          const isOnline =
            window.online_users && window.online_users.includes(friend.friend.id.toString());
          const stats = board.get(friend.friend.id) || { total_games: 0, total_wins: 0, ratio: 0 };
          return `
              <div class="row p-1 rounded-1 justify-content-between align-items-center mb-2 glass-effect" style="cursor: pointer;" id="friend-${esc(friend.friend.id)}">
                <div class="col-3 col-md-4">
                  <div class="d-flex align-items-center">
                    <div class="position-relative">
                      <img src="${esc(friend.friend.profile.avatar)}" class="img-fluid rounded-circle" width="35" style="width: 35px; height: 35px;" alt="user profile image">
                      <div class="user-status ${isOnline ? "online" : ""}"></div>
                    </div>
                    <div class="ps-2">
                      <a href="/friend/${esc(friend.friend.profile.uuid)}" data-link><span class="fw-bold text-capitalize" style="font-size: 14px;">${esc(friend.friend.username)}</span></a>
                    </div>
                  </div>
                </div>
                <div class="col-2 pe-2 ">
                  <span class="friend-total"><strong>${esc(stats.total_games)}</strong></span>
                </div>
                <div class="col-2 pe-2 ">
                  <span class="friend-wins"><strong>${esc(stats.total_wins)}</strong></span>
                </div>
                <div class="col-2 pe-2 d-none d-md-block">
                  <span class="friend-ratio"><strong>${esc(stats.ratio)}%</strong></span>
                </div>
                <div class="col-3 col-md-2 text-end">
                  <a data-id="${esc(friend.friend.id)}" role="button" class="bg-success font-glitch text-white text-decoration-none p-1">PLAY</a>
                </div>
              </div>
          `;
        })
        .join("");
    } catch (e) {
      console.error(e);
    } finally {
      hideOverlay();
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
      console.error(error);
    }
  }

  async unblockFriend(e) {
    try {
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
      if (response.ok) this.getBlockedFriends();
    } catch (error) {
      console.error(error);
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
      console.error(error);
    }
  }
}

window.customElements.define("user-profile", ProfilePage);

export { ProfilePage };
