import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Page } from "../core/page.js";
import { session } from "../core/session.js";

const player = (row, index) => html`
  <div class="d-flex p-2 justify-content-between align-items-center glass-effect mb-2">
    <div class="col-2">
      <img src="/static/asset/images/rank${index + 1}.png" alt="Rank ${index + 1}" width="30" />
    </div>
    <div class="col-4">
      <div class="d-flex align-items-center">
        <img
          src="${row.user.avatar}"
          class="img-fluid rounded-circle d-none d-md-block"
          alt=""
          style="width:35px; height:35px"
        />
        <div class="ps-2">
          <span class="fw-bold text-capitalize" style="font-size: 14px;">${row.user.username}</span>
        </div>
      </div>
    </div>
    <div class="col-3 col-md-2 text-center text-md-left"><strong>${row.total_games}</strong></div>
    <div class="col-3 col-md-2 text-center text-md-left"><strong>${row.total_wins}</strong></div>
    <div class="col-2 d-none d-md-block text-center"><strong>${row.ratio}%</strong></div>
  </div>
`;

const view = (user) => html`
  <main-nav></main-nav>
  <section>
    <div class="container px-4 px-md-0">
      <div class="row" style="color: var(--darker);">
        <div class="d-flex  p-4  mt-4  rounded-1 font-monospace justify-content-between align-items-center"
          style="background-color: #624E88;">
          <div class="welcome" style="font-size: 1rem;">
            <h1 class="m-0 text-capitalize">Welcome Back, <span id="firstName">${user.first_name}</span></h1>
            <p class="text-capitalize vt323-regular" style="font-size: 24px;">Embrace the opportunity to join our
              world and savor every moment.</p>
          </div>
          <div class="welcome-img d-none d-md-block">
            <img src="/static/asset/images/robots_welcome.svg" class="img-fluid" width="120" alt="a robots waving"
              style="max-width: 100%;">
          </div>
        </div>
      </div>
      <div
        class="row p-3 mt-5 Cards justify-content-evenly flex-column align-items-center align-items-md-stretch flex-md-row">
        <h2 class="font-monospace">Games Modes</h2>

        <div class="newCard d-flex align-items-center  mb-4 me-md-4">

          <div class="content__ me-2" style="width: 50%;">
            <h6 class="fw-bold text-uppercase" style="color: var(--darker);">AI</h6>
            <p style="font-size: 13px;">Play against AI </p>
            <a data-link href="/play/bot" class="play px-3 py-1 fw-bold text-uppercase" data-play style="color: var(--darker); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);">
              Play
            </a>
          </div>
          <div class="image " style="width: 50%;">
            <img src="/static/asset/images/racket-ball.png" class="img-fluid" alt="">
          </div>
        </div>

        <div class="newCard d-flex align-items-center  mb-4 me-md-4">

          <div class="content__ me-2" style="width: 50%;">
            <h6 class="fw-bold text-uppercase" style="color: var(--darker);">Classic</h6>
            <p style="font-size: 13px;">Find you a rival </p>
            <a data-link href="/matchmaking" class="play px-3 py-1 fw-bold text-uppercase" data-play style="color: var(--darker); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);">
              Play
            </a>
          </div>
          <div class="image " style="width: 50%;">
            <img src="/static/asset/images/racket-ball.png" class="img-fluid" alt="">
          </div>
        </div>

        <div class="newCard d-flex align-items-center mb-4 me-md-4">

          <div class="content__ me-2" style="width: 50%;">
            <h6 class="fw-bold text-uppercase" style="color: var(--darker);">Tournament</h6>
            <p style="font-size: 13px;">Grind & win the trophy</p>
            <a data-link href="/tournament" class="play px-3 py-1 fw-bold text-uppercase" data-play style="color: var(--darker); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);">
              Play
            </a>
          </div>
          <div class="image " style="width: 50%;">
            <img src="/static/asset/images/throphy.png" class="img-fluid" alt="">
          </div>
        </div>

        <div class="newCard d-flex align-items-center mb-4  me-md-4">

          <div class="content__ me-2" style="width: 50%;">
            <h6 class="fw-bold text-uppercase" style="color: var(--darker);">Friend</h6>
            <p style="font-size: 13px;">Challenge your friend </p>
            <a href="/profile" class="play px-3 py-1 fw-bold text-uppercase" data-link data-play style="color: var(--darker); background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);">
              Play
            </a>
          </div>
          <div class="image " style="width: 50%;">
            <img src="/static/asset/images/ping-pong-rackets-ball-isolated(1).png" class="img-fluid" alt="">
          </div>
        </div>
      </div>
      <div class="row justify-content-center p-3 mb-2">
        <h2 class="font-monospace">Best Players</h2>
        <div class="col-12 col-lg-10 glass-effect p-2" id="bestPlayer">
          <div class="d-flex p-2  justify-content-between align-items-center mb-1">
            <div class="col-2"><strong>Rank</strong></div>
            <div class="col-4"><strong>Username</strong> </div>
            <div class="col-3 col-md-2 text-center text-md-left"><strong>Total</strong></div>
            <div class="col-3 col-md-2 text-center text-md-left"><strong>Wins</strong></div>
            <div class="col-2 d-none d-md-block text-center"><strong>Ratio</strong></div>
          </div>
<div id="best-players"></div>
        </div>

      </div>

    </div>
  </section>
  </div>
`;

/** The logged-in home: game modes and the three best players. */
class HomePage extends Page {
  async mount() {
    this.render(view(session.user));
    const result = await this.api.get("/api/game/leaderboard/");
    if (!toastOnError(result)) return;
    const top = result.data.users.slice(0, 3).map(player);
    render(this.querySelector("#best-players"), html`${top}`);
  }
}

customElements.define("user-home", HomePage);
