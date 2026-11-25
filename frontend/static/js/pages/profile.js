import { historyRow, playableHistory, showStats } from "../components/player.js";
import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { overlay } from "../core/overlay.js";
import { Page } from "../core/page.js";
import { session } from "../core/session.js";
import { presence } from "../core/store.js";
import { inviteToGame } from "../services/game.js";

const view = (user) => html`
  <section class="">
    <main-nav></main-nav>
    <div class="container-md px-4 mt-4">
      <div class="row p-3  text-white  glass-effect">
        <div class="col-12 col-md-6 col-lg-6 mx-auto">
          <div class="d-lg-flex align-items-center  text-center text-lg-start pb-3 pb-lg-0">
            <div class="profile-image">
              <img
                src="${user.profile.avatar}"
                class="rounded rounded-circle"
                width="120"
                height="120"
                alt="user profile image"
                id="user-img"
              />
            </div>
            <div class="ps-0 ps-md-4 pt-4 pb-md-0">
              <h4 class="m-0 fw-bold text-capitalize" id="fullName">
                ${user.first_name} ${user.last_name}
              </h4>
              <span class="fw-medium text-capitalize" id="username">@${user.username}</span>
            </div>
          </div>
        </div>

        <div class="rank col-6  d-lg-flex d-none align-items-center justify-content-end">
          <div class="match-ratio me-4">
            <span class="d-block mb-1">
              <i class="fa-solid fa-ranking-star fa-xl text-secondary"></i>
            </span>
            <span class="fw-bold"> <strong id="profile-rank" aria-label="Rank">-</strong></span>
          </div>
        </div>
      </div>

      <div class="row my-4">
        <div class="col-12 col-md-6 col-lg-3 mb-4 mb-lg-0">
          <div class="status-card  work mx-auto">
            <div class="img-section">
              <svg xmlns="http://www.w3.org/2000/svg" height="77" width="76">
                <path
                  fill-rule="nonzero"
                  fill="#3F9CBB"
                  d="m60.91 71.846 12.314-19.892c3.317-5.36 3.78-13.818-2.31-19.908l-26.36-26.36c-4.457-4.457-12.586-6.843-19.908-2.31L4.753 15.69c-5.4 3.343-6.275 10.854-1.779 15.35a7.773 7.773 0 0 0 7.346 2.035l7.783-1.945a3.947 3.947 0 0 1 3.731 1.033l22.602 22.602c.97.97 1.367 2.4 1.033 3.732l-1.945 7.782a7.775 7.775 0 0 0 2.037 7.349c4.49 4.49 12.003 3.624 15.349-1.782Zm-24.227-46.12-1.891-1.892-1.892 1.892a2.342 2.342 0 0 1-3.312-3.312l1.892-1.892-1.892-1.891a2.342 2.342 0 0 1 3.312-3.312l1.892 1.891 1.891-1.891a2.342 2.342 0 0 1 3.312 3.312l-1.891 1.891 1.891 1.892a2.342 2.342 0 0 1-3.312 3.312Zm14.19 14.19a2.343 2.343 0 1 1 3.315-3.312 2.343 2.343 0 0 1-3.314 3.312Zm0 7.096a2.343 2.343 0 0 1 3.313-3.312 2.343 2.343 0 0 1-3.312 3.312Zm7.096-7.095a2.343 2.343 0 1 1 3.312 0 2.343 2.343 0 0 1-3.312 0Zm0 7.095a2.343 2.343 0 0 1 3.312-3.312 2.343 2.343 0 0 1-3.312 3.312Z"
                ></path>
              </svg>
            </div>

            <div class="card-desc">
              <div class="card-header">
                <div class="card-title">Played</div>

                <div class="card-menu">
                  <div class="dot"></div>
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
              <div class="card-stats total">0 Match</div>
              <!-- <p class="recent">Last Week-36hrs</p> -->
            </div>
          </div>
        </div>
        <div class="col-12 col-md-6 col-lg-3 mb-4 mb-md-0">
          <div class="status-card  work mx-auto">
            <div class="img-section">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="77" width="76">
                <path
                  fill-rule="nonzero"
                  fill="#3F9CBB"
                  d="M4.1 38.2C1.4 34.2 0 29.4 0 24.6C0 11 11 0 24.6 0L133.9 0c11.2 0 21.7 5.9 27.4 15.5l68.5 114.1c-48.2 6.1-91.3 28.6-123.4 61.9L4.1 38.2zm503.7 0L405.6 191.5c-32.1-33.3-75.2-55.8-123.4-61.9L350.7 15.5C356.5 5.9 366.9 0 378.1 0L487.4 0C501 0 512 11 512 24.6c0 4.8-1.4 9.6-4.1 13.6zM80 336a176 176 0 1 1 352 0A176 176 0 1 1 80 336zm184.4-94.9c-3.4-7-13.3-7-16.8 0l-22.4 45.4c-1.4 2.8-4 4.7-7 5.1L168 298.9c-7.7 1.1-10.7 10.5-5.2 16l36.3 35.4c2.2 2.2 3.2 5.2 2.7 8.3l-8.6 49.9c-1.3 7.6 6.7 13.5 13.6 9.9l44.8-23.6c2.7-1.4 6-1.4 8.7 0l44.8 23.6c6.9 3.6 14.9-2.2 13.6-9.9l-8.6-49.9c-.5-3 .5-6.1 2.7-8.3l36.3-35.4c5.6-5.4 2.5-14.8-5.2-16l-50.1-7.3c-3-.4-5.7-2.4-7-5.1l-22.4-45.4z"
                />
              </svg>
            </div>

            <div class="card-desc">
              <div class="card-header">
                <div class="card-title">Wins</div>

                <div class="card-menu">
                  <div class="dot"></div>
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
              <div class="card-stats wins">0 Match</div>
              <!-- <p class="recent">Last Week-36hrs</p> -->
            </div>
          </div>
        </div>
        <div class="col-12 col-md-6 col-lg-3 mb-4 mb-md-0">
          <div class="status-card  work mx-auto">
            <div class="img-section">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="77" width="76">
                <path
                  fill-rule="nonzero"
                  fill="#3F9CBB"
                  d="M459.1 52.4L442.6 6.5C440.7 2.6 436.5 0 432.1 0s-8.5 2.6-10.4 6.5L405.2 52.4l-46 16.8c-4.3 1.6-7.3 5.9-7.2 10.4c0 4.5 3 8.7 7.2 10.2l45.7 16.8 16.8 45.8c1.5 4.4 5.8 7.5 10.4 7.5s8.9-3.1 10.4-7.5l16.5-45.8 45.7-16.8c4.2-1.5 7.2-5.7 7.2-10.2c0-4.6-3-8.9-7.2-10.4L459.1 52.4zm-132.4 53c-12.5-12.5-32.8-12.5-45.3 0l-2.9 2.9C256.5 100.3 232.7 96 208 96C93.1 96 0 189.1 0 304S93.1 512 208 512s208-93.1 208-208c0-24.7-4.3-48.5-12.2-70.5l2.9-2.9c12.5-12.5 12.5-32.8 0-45.3l-80-80zM200 192c-57.4 0-104 46.6-104 104l0 8c0 8.8-7.2 16-16 16s-16-7.2-16-16l0-8c0-75.1 60.9-136 136-136l8 0c8.8 0 16 7.2 16 16s-7.2 16-16 16l-8 0z"
                />
              </svg>
            </div>

            <div class="card-desc">
              <div class="card-header">
                <div class="card-title">Loses</div>

                <div class="card-menu">
                  <div class="dot"></div>
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
              <div class="card-stats losses">0 Match</div>
              <!-- <p class="recent">Last Week-36hrs</p> -->
            </div>
          </div>
        </div>
        <div class="col-12 col-md-6 col-lg-3">
          <div class="status-card  work mx-auto">
            <div class="img-section">
              <!-- <svg xmlns="http://www.w3.org/2000/svg" height="77" width="76"><path fill-rule="nonzero" fill="#3F9CBB" d="m60.91 71.846 12.314-19.892c3.317-5.36 3.78-13.818-2.31-19.908l-26.36-26.36c-4.457-4.457-12.586-6.843-19.908-2.31L4.753 15.69c-5.4 3.343-6.275 10.854-1.779 15.35a7.773 7.773 0 0 0 7.346 2.035l7.783-1.945a3.947 3.947 0 0 1 3.731 1.033l22.602 22.602c.97.97 1.367 2.4 1.033 3.732l-1.945 7.782a7.775 7.775 0 0 0 2.037 7.349c4.49 4.49 12.003 3.624 15.349-1.782Zm-24.227-46.12-1.891-1.892-1.892 1.892a2.342 2.342 0 0 1-3.312-3.312l1.892-1.892-1.892-1.891a2.342 2.342 0 0 1 3.312-3.312l1.892 1.891 1.891-1.891a2.342 2.342 0 0 1 3.312 3.312l-1.891 1.891 1.891 1.892a2.342 2.342 0 0 1-3.312 3.312Zm14.19 14.19a2.343 2.343 0 1 1 3.315-3.312 2.343 2.343 0 0 1-3.314 3.312Zm0 7.096a2.343 2.343 0 0 1 3.313-3.312 2.343 2.343 0 0 1-3.312 3.312Zm7.096-7.095a2.343 2.343 0 1 1 3.312 0 2.343 2.343 0 0 1-3.312 0Zm0 7.095a2.343 2.343 0 0 1 3.312-3.312 2.343 2.343 0 0 1-3.312 3.312Z"></path></svg> -->
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" height="77" width="76">
                <path
                  fill-rule="nonzero"
                  fill="#3F9CBB"
                  d="M522.1 62.4c16.8-5.6 25.8-23.7 20.2-40.5S518.6-3.9 501.9 1.6l-113 37.7C375 15.8 349.3 0 320 0c-44.2 0-80 35.8-80 80c0 3 .2 5.9 .5 8.8L117.9 129.6c-16.8 5.6-25.8 23.7-20.2 40.5s23.7 25.8 40.5 20.2l135.5-45.2c4.5 3.2 9.3 5.9 14.4 8.2L288 480c0 17.7 14.3 32 32 32l192 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-160 0 0-294.7c21-9.2 37.2-27 44.2-49l125.9-42zM439.6 288L512 163.8 584.4 288l-144.9 0zM512 384c62.9 0 115.2-34 126-78.9c2.6-11-1-22.3-6.7-32.1L536.1 109.8c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8L392.7 273.1c-5.7 9.8-9.3 21.1-6.7 32.1C396.8 350 449.1 384 512 384zM129.2 291.8L201.6 416 56.7 416l72.4-124.2zM3.2 433.1C14 478 66.3 512 129.2 512s115.2-34 126-78.9c2.6-11-1-22.3-6.7-32.1L153.2 237.8c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8L9.9 401.1c-5.7 9.8-9.3 21.1-6.7 32.1z"
                />
              </svg>
            </div>

            <div class="card-desc">
              <div class="card-header">
                <div class="card-title">Ratio</div>

                <div class="card-menu">
                  <div class="dot"></div>
                  <div class="dot"></div>
                  <div class="dot"></div>
                </div>
              </div>
              <div class="card-stats ratio">0%</div>
            </div>
          </div>
        </div>
      </div>
      <div class="row justify-content-between">
        <div class="col-12 col-lg-6">
          <h3>Game history</h3>
          <div class="row glass-effect p-1" style="height: 550px; overflow-y: auto">
            <div class="profile-content" id="games-container"></div>
          </div>
        </div>
        <div class="col-12 col-lg-5">
          <h3 class="mt-2">Friends</h3>
          <div class="row mb-2 glass-effect p-2" style="height: 300px; overflow-y: auto">
            <div id="friend-container">
              <div class="row mb-2">
                <div class="col-3 col-md-4"><strong>Username</strong></div>
                <div class="col-1 col-md-2"><strong>Total</strong></div>
                <div class="col-1 col-md-2"><strong>Wins</strong></div>
                <div class="col-2 d-none d-md-block"><strong>Ratio</strong></div>
                <div class="col-3 col-md-2 text-end"><strong>Game</strong></div>
              </div>
            </div>
          </div>
          <h3>Blocked Friends</h3>
          <div class="row glass-effect p-2 mb-2" style="height: 200px; overflow-y: auto;">
            <div id="blocked-container"></div>
          </div>
        </div>
      </div>
    </div>
  </section>
`;

const friendRow = (friend, stats, online) => html`
  <div
    class="row p-1 rounded-1 justify-content-between align-items-center mb-2 glass-effect"
    id="friend-${friend.id}"
    data-user="${friend.id}"
  >
    <div class="col-3 col-md-4">
      <div class="d-flex align-items-center">
        <div class="position-relative">
          <img
            src="${friend.profile.avatar}"
            class="img-fluid rounded-circle"
            width="35"
            style="width: 35px; height: 35px;"
            alt=""
          />
          <div class="user-status ${online ? "online" : ""}"></div>
        </div>
        <div class="ps-2">
          <a href="/friend/${friend.profile.uuid}" data-link>
            <span class="fw-bold text-capitalize" style="font-size: 14px;">${friend.username}</span>
          </a>
        </div>
      </div>
    </div>
    <div class="col-2 pe-2">
      <span class="friend-total"><strong>${stats.total_games}</strong></span>
    </div>
    <div class="col-2 pe-2">
      <span class="friend-wins"><strong>${stats.total_wins}</strong></span>
    </div>
    <div class="col-2 pe-2 d-none d-md-block">
      <span class="friend-ratio"><strong>${stats.ratio}%</strong></span>
    </div>
    <div class="col-3 col-md-2 text-end">
      <button
        type="button"
        data-invite="${friend.id}"
        class="btn bg-success font-glitch text-white p-1"
        aria-label="Invite ${friend.username} to a game"
      >
        PLAY
      </button>
    </div>
  </div>
`;

const blockedRow = (user) => html`
  <div class="row p-1 rounded-1 justify-content-between align-items-center mb-2 glass-effect">
    <div class="col-6">
      <div class="d-flex align-items-center">
        <img
          src="${user.profile.avatar}"
          class="img-fluid rounded-circle"
          width="35"
          style="width: 35px; height: 35px"
          alt=""
        />
        <div class="ps-2">
          <span class="fw-bold text-capitalize" style="font-size: 14px;">${user.username}</span>
        </div>
      </div>
    </div>
    <div class="col-4 text-end">
      <button type="button" data-unblock="${user.id}" class="btn btn-block bg-danger p-1">
        Unblock
      </button>
    </div>
  </div>
`;

/** Your profile: stats, match history, friends (with stats and rank), blocked users. */
class ProfilePage extends Page {
  async mount() {
    this.render(view(session.user));
    this.on(this.querySelector("#friend-container"), "click", (event) => {
      const button = event.target.closest("[data-invite]");
      if (button) inviteToGame(this.api, button.dataset.invite);
    });
    this.on(this.querySelector("#blocked-container"), "click", (event) => {
      const button = event.target.closest("[data-unblock]");
      if (button) this.unblock(button.dataset.unblock);
    });
    this.subscribe(presence, (online) => this.showOnline(online));
    overlay.show();
    try {
      await Promise.all([this.loadFriends(), this.loadBlocked(), this.loadHistory()]);
    } finally {
      overlay.hide();
    }
  }

  // Games, wins and ratio of every player come from the leaderboard (the
  // friends API has none), and its order gives the rank.
  async loadFriends() {
    const [friends, board] = await Promise.all([
      this.api.get("/api/friends/"),
      this.api.get("/api/game/leaderboard/"),
    ]);
    const stats = new Map(
      (board.ok ? board.data.users : []).map((row, index) => [
        row.user.id,
        { ...row, rank: index + 1 },
      ]),
    );
    const rank = stats.get(session.user.id)?.rank;
    this.querySelector("#profile-rank").textContent = rank ? `#${rank}` : "-";
    if (!toastOnError(friends)) return;
    const online = presence.get();
    const none = { total_games: 0, total_wins: 0, ratio: 0 };
    render(
      this.querySelector("#friend-container"),
      html`${friends.data.map(({ friend }) =>
        friendRow(friend, stats.get(friend.id) || none, online.has(String(friend.id))),
      )}`,
    );
  }

  async loadBlocked() {
    const result = await this.api.get("/api/friends/blocked/");
    if (!toastOnError(result)) return;
    render(
      this.querySelector("#blocked-container"),
      html`${result.data.map((b) => blockedRow(b.friend))}`,
    );
  }

  async unblock(userId) {
    const result = await this.api.post("/api/friends/unblock/", { user_id: userId });
    if (toastOnError(result)) this.loadBlocked();
  }

  async loadHistory() {
    const result = await this.api.get("/api/game/history/");
    if (!toastOnError(result)) return;
    showStats(this, result.data.stats);
    render(
      this.querySelector("#games-container"),
      html`${playableHistory(result.data.games).map(historyRow)}`,
    );
  }

  showOnline(online) {
    for (const row of this.querySelectorAll("[data-user]")) {
      row.querySelector(".user-status")?.classList.toggle("online", online.has(row.dataset.user));
    }
  }
}

customElements.define("user-profile", ProfilePage);
