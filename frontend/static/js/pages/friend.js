import { historyRow, playableHistory, showStats } from "../components/player.js";
import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { overlay } from "../core/overlay.js";
import { Page } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";

const view = () => html`
  <main-nav></main-nav>
  <section>
    <div class="container-md mt-4 px-4">
      <div class="row p-1 p-md-3  text-white box-sh-1 secondary-bg">
        <div class="col-12 col-md-6 col-lg-6 mx-auto">
          <div class="d-md-flex align-items-center  text-center text-md-start pb-3 pb-lg-0">
            <div class="profile-image">
              <img
                src="/static/asset/images/profile.svg"
                class="img-fluid rounded rounded-circle"
                width="120"
                alt="user profile image"
                id="user-img"
              />
            </div>
            <div class="ps-0 ps-md-4 pt-3 pb-md-0">
              <h4 class="m-0 fw-bold text-capitalize" id="fullName"></h4>
              <span class="fw-medium text-capitalize" id="username"></span>
            </div>
          </div>
        </div>
        <div
          class="col-12 col-md-6  d-flex align-items-center justify-content-center  justify-content-md-end mb-2 mb-md-0"
        >
          <button
            class="d-flex align-items-center btn btn-block bg-primary  me-2 text-truncate text-white"
            id="add-friend"
          >
            <i class="fa-solid fa-plus me-2"></i> Friend
          </button>
          <a
            href="/chat"
            data-link
            class="d-flex align-items-center btn btn-block text-white me-2"
            style=" background-color: #BE8CE4;"
            ><i class="fa-solid fa-message me-2"></i>Message</a
          >
          <button
            class="d-flex align-items-center btn btn-block text-white shadow"
            aria-label="Block"
            id="block"
          >
            <i class="fa-solid fa-lg fa-triangle-exclamation"></i>
          </button>
        </div>
      </div>
      <div class="row my-4">
        <div class="col-12 col-md-6 col-lg-3 mb-4 mb-md-0">
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
        <div class="col-12 col-md-6 col-lg-3 mb-4 mb-md-0">
          <div class="status-card  work mx-auto">
            <div class="img-section">
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

      <div class="row mt-4 mb-2 justify-content-between">
        <div
          class="col-12 p-3 glass-effect mb-3 mb-lg-0 justify-content-center"
          style="min-height: 47vh;"
        >
          <h2 class="text-white">Game History</h2>
          <div class="row justify-content-center">
            <div class="col-12 col-md-9" id="friend-history"></div>
          </div>
        </div>
      </div>
    </div>
  </section>
`;

// What the friend button shows and does for each relationship.
const BUTTON = {
  add: { icon: "fa-plus", label: "Friend", disabled: false },
  pending: { icon: "fa-user-clock", label: "pending", disabled: true },
  accept: { icon: "fa-user-plus fa-sm", label: "accept", disabled: false },
  friends: { icon: "fa-user-check", label: "friends", disabled: true },
};

/** Another player's profile (/friend/:uuid): stats, history, friend and block buttons. */
class FriendPage extends Page {
  async mount() {
    const { uuid } = this.params;
    if (uuid === session.user.profile.uuid) {
      navigate("/profile", { replace: true });
      return;
    }
    this.render(view());
    this.button = this.querySelector("#add-friend");
    this.on(this.button, "click", () => this.onFriendButton());
    this.on(this.querySelector("#block"), "click", () => this.block());
    overlay.show();
    try {
      await this.load(uuid);
    } finally {
      overlay.hide();
    }
  }

  async load(uuid) {
    // All four answers before deciding: the relationship comes from three lists.
    const [profile, friends, sent, received] = await Promise.all([
      this.api.get(`/api/auth/profile/${encodeURIComponent(uuid)}/`),
      this.api.get("/api/friends/"),
      this.api.get("/api/friends/sent-requests/"),
      this.api.get("/api/friends/requests/"),
    ]);
    if (!toastOnError(profile)) {
      if (profile.status === 404) navigate("/home", { replace: true });
      return;
    }
    this.friend = profile.data.user;
    this.querySelector("#fullName").textContent =
      `${this.friend.first_name} ${this.friend.last_name}`;
    this.querySelector("#username").textContent = `@${this.friend.username}`;
    this.querySelector("#user-img").src = this.friend.profile.avatar;
    showStats(this, profile.data.stats);
    render(
      this.querySelector("#friend-history"),
      html`${playableHistory(profile.data.history).map(historyRow)}`,
    );

    const listed = (result) => result.ok && result.data.some((f) => f.friend.profile.uuid === uuid);
    if (listed(friends)) this.setState("friends");
    else if (listed(sent)) this.setState("pending");
    else if (listed(received)) this.setState("accept");
    else this.setState("add");
  }

  setState(state) {
    this.state = state;
    const { icon, label, disabled } = BUTTON[state];
    render(this.button, html`<i class="fa-solid ${icon} me-2"></i> ${label}`);
    this.button.disabled = disabled;
  }

  async onFriendButton() {
    if (!this.friend) return;
    if (this.state === "accept") {
      const result = await this.api.post("/api/friends/accept/", { source_user: this.friend.id });
      if (toastOnError(result)) this.setState("friends");
    } else if (this.state === "add") {
      const result = await this.api.post("/api/friends/send/", { target_user: this.friend.id });
      if (toastOnError(result)) this.setState("pending");
    }
  }

  async block() {
    if (!this.friend) return;
    const result = await this.api.post("/api/friends/block/", { user_id: this.friend.id });
    if (toastOnError(result)) navigate("/home");
  }
}

customElements.define("friend-page", FriendPage);
