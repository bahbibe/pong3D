import { escapeHTML as esc } from "../escape.js";
import { AbstractPage } from "./AbstarctPage.js";
import { BASE_URL } from "../router.js";
class Home extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-home");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    const first_name = this.querySelector("#firstName");

    const user = window.user;
    first_name.textContent = `${user.first_name}`;
    this.render();
  }

  async render() {
    try {
      const response = await fetch(`${BASE_URL}/api/game/leaderboard/`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
      const data = await response.json();
      if (response.ok) {
        const bestPlayer = this.querySelector("#bestPlayer");
        const users = data.data.users;

        for (const [index, user] of users.entries()) {
          if (index < 3) {
            bestPlayer.innerHTML += `
              <div class="d-flex p-2 justify-content-between align-items-center glass-effect mb-2">
                  <div class="col-2"><img src="/static/asset/images/rank${index + 1}.png" alt="badge Rank number one" width="30"></div>
                  <div class="col-4">
                    <div class="d-flex align-items-center">
                      <img src="${esc(user.user.avatar)}" class="img-fluid rounded-circle d-none d-md-block" alt="user profile image" style="width:35px; height:35px">
                      <div class="ps-2">
                        <span class="fw-bold text-capitalize" style="font-size: 14px;">${esc(user.user.username)}</span>
                      </div>
                    </div>
                  </div>
                  <div class="col-3 col-md-2 text-center text-md-left"><strong>${esc(user.total_games)}</strong></div>
                  <div class="col-3 col-md-2 text-center text-md-left"><strong>${esc(user.total_wins)}</strong></div>
                  <div class="col-2 d-none d-md-block text-center"><strong>${esc(user.ratio)}%</strong></div>
              </div>
          `;
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

window.customElements.define("user-home", Home);

export { Home };
