import { escapeHTML as esc } from "../escape.js";
import { AbstractPage } from "./AbstarctPage.js";
import { showOverlay, hideOverlay } from "../helpers.js";
import { navigateTo } from "../router.js";
import { BASE_URL } from "../router.js";

class RankingPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("ranking-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
  }

  async render() {
    try {
      const response = await fetch(`${BASE_URL}/api/game/leaderboard/`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      const data = await response.json();
      console.log(data);
      if (response.ok) {
        const ranking = this.querySelector("tbody");
        const users = data.data.users;
        users.forEach((user, index) => {
          ranking.innerHTML += `
            <tr>
                <th scope="row">${index + 1}</th>
                <td>
                <a href="">
                  <div class="user-cell">
                    <img src="${esc(user.user.avatar)}" alt="">
                    <div class="username">${esc(user.user.username)}</div>
                  </div>
                </a>
                </td>
                <td>${esc(user.total_games)}</td>
                <td>${esc(user.total_wins)}</td>
                <td>${esc(user.total_losses)}</td>
                <td>${esc(user.ratio)}</td>
            </tr>
          `;
        });
      }
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

window.customElements.define("ranking-page", RankingPage);

export { RankingPage };
