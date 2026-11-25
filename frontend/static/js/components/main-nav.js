import "./notifications-menu.js";
import "./search-bar.js";
import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { Component } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";

const view = (user) => html`
  <nav class="navbar navbar-expand d-flex justify-content-between">
    <a href="/home" data-link>
      <img src="/static/asset/images/transistor-ping-pong.gif" width="60" alt="pong3D home" />
    </a>
    <search-bar class="d-none d-md-flex"></search-bar>

    <div class="d-flex align-items-center">
      <notifications-menu></notifications-menu>

      <div class="dropdown">
        <div
          class="user d-flex align-items-center mb-2 rounded-pill secondary-bg px-3 py-2 shadow "
          style="cursor: pointer;"
        >
          <img
            src="${user.profile.avatar}"
            class="rounded-circle"
            style="width: 40px; height: 40px;"
            alt="user profile image"
            loading="lazy"
            id="nav-user-img"
          />
          <strong class="d-none d-sm-block ms-2" id="nav-username" style="cursor: pointer;"
            >${user.username}</strong
          >
        </div>
        <ul class="dropdown-content ">
          <li>
            <a class="" href="/home" id="home" data-link>
              <i class="fa-solid fa-house me-1"></i>
              Home
            </a>
          </li>
          <li>
            <a href="/profile" id="profile" data-link>
              <i class="fa-solid fa-user me-1"></i>
              Profile
            </a>
          </li>
          <li>
            <a href="/ranking" id="ranking" data-link>
              <i class="fa-solid fa-ranking-star me-1"></i>
              Leaderboard
            </a>
          </li>
          <li>
            <a class="" href="/chat" id="chat" data-link>
              <i class="fa-regular fa-comment-dots me-1"></i>
              Chat
            </a>
          </li>
          <li>
            <a class="" href="/settings" id="settings" data-link>
              <i class="fa-solid fa-gear me-1"></i>
              Settings
            </a>
          </li>
          <li>
            <a class="" href="#" id="logout">
              <i class="fa-solid fa-arrow-right-from-bracket me-1"></i>
              Exit
            </a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
`;

class MainNav extends Component {
  mount() {
    this.render(view(session.user));
    this.on(this.querySelector("#logout"), "click", (event) => {
      // href="#": following it would fire popstate and render the page again.
      event.preventDefault();
      this.logout();
    });
  }

  async logout() {
    const result = await this.api.post("/api/auth/logout/");
    if (!toastOnError(result)) return;
    session.clear();
    navigate("/login");
  }
}

customElements.define("main-nav", MainNav);
