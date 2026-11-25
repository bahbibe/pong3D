import { html } from "../core/html.js";
import { Page } from "../core/page.js";

// The public landing page (/).
const view = () => html`
  <section class="m-2">
    <div class="container-md">
      <h1 class="vt323-regular display-1 text-center border-bottom fw-bold">PO-NG</h1>
      <div class="pong-history row justify-content-between align-items-center p-3">
        <h2 class="vt323-regular display-3 fw-bold mt-3">Pong History</h2>
        <div class="image col-12 col-lg-6">
          <img
            src="/static/asset/images/1970-pong.png"
            class="img-fluid"
            alt="The original 1970s Pong"
          />
        </div>
        <div class="description vt323-regular fs-4 p-3 col-12 col-lg-5">
          <h2>1972: Birth of Atari Pong</h2>
          <p>
            The year 1972 marked a pivotal moment in gaming history with the release of "Pong" by
            Atari, developed by Nolan Bushnell and Allan Alcorn. It became the first commercially
            successful video game, captivating audiences with its simple yet addictive gameplay.
            Pong simulated table tennis, featuring two paddles and a bouncing ball, controlled by
            players using dials. Its success sparked the arcade gaming revolution, laying the
            foundation for the industry we know today.
          </p>
          <a
            href="/login"
            data-link
            class="join-btn btn btn-block bg-black text-white text-uppercase fs-3 px-4"
            >join us</a
          >
        </div>
      </div>
      <div class="developer row justify-content-between align-items-center">
        <h2 class="vt323-regular display-3 divider col-12">Developers</h2>
        <div class="description vt323-regular fs-4 p-3 col-12 col-lg-6">
          <p>
            The developers of this project are a group of students from 1337 School, who are
            passionate about programming and game development. They have worked together to create
            this project as part of their curriculum, showcasing their skills and creativity.
          </p>
        </div>
        <div class="image col-12 col-lg-5">
          <img src="/static/asset/images/cluster.jpg" class="img-fluid" alt="1337 coding cluster" />
        </div>
        <div class="team col-12 col-lg-6 p-3"></div>
      </div>
      <div class="our-team mb-5 row d-flex justify-content-between">
        <h2 class="vt323-regular display-3 divider">our team</h2>
        <div class="team-member text-center col-12 mb-4 col-md-6 col-lg-3">
          <img
            src="/static/asset/images/bmakhlou.jpeg"
            class="img-fluid rounded-circle"
            alt="team member"
            width="200"
          />
          <h4 class="vt323-regular fs-3 m-0 p-0">Bilal Makhloufi</h4>
          <p class="vt323-regular fs-4 m-0  p-0 text-info-emphasis text-capitalize">
            Front-end Developer
          </p>
        </div>
        <div class="team-member text-center col-12 mb-4 col-md-6 col-lg-3">
          <img
            src="/static/asset/images/mahansal.JPG"
            class="img-fluid rounded-circle"
            alt="team member"
            width="200"
          />
          <h4 class="vt323-regular fs-3 m-0 p-0">Marwane Ahansal</h4>
          <p class="vt323-regular fs-4 m-0  p-0 text-info-emphasis text-capitalize">
            fullstack Developer
          </p>
        </div>
        <div class="team-member text-center col-12 mb-4 col-md-6 col-lg-3">
          <img
            src="/static/asset/images/bahbibe.JPG"
            class="img-fluid rounded-circle"
            alt="team member"
            width="200"
          />
          <h4 class="vt323-regular fs-3 m-0 p-0 ">Boubker Ahbibe</h4>
          <p class="vt323-regular fs-4 m-0  p-0 text-info-emphasis text-capitalize">
            fullstack Developer
          </p>
        </div>
        <div class="team-member text-center col-12 mb-4 col-md-6 col-lg-3">
          <img
            src="/static/asset/images/abeihaqi.JPG"
            class="img-fluid rounded-circle"
            alt="team member"
            width="200"
          />
          <h4 class="vt323-regular fs-3 m-0 p-0">Amine Beihaqi</h4>
          <p class="vt323-regular fs-4 m-0  p-0 text-info-emphasis text-capitalize">
            fullstack Developer
          </p>
        </div>
      </div>

      <div class="purpose mb-5">
        <h3 class="vt323-regular  display-3 fw-bold mt-3">About pong and its purpose</h3>
        <p class="vt323-regular fs-3">
          "PO-NG" is an independent non-commercial project created for entertainment and educational
          purposes. It is obviously inspired by the classic game "Pong" but it is indeed a
          completely separate creation.
        </p>
      </div>
      <div class="footer border-top">
        <p class="vt323-regular fs-3 text-center">© 2024 PONG. All rights reserved.</p>
      </div>
    </div>
  </section>
`;

class LandingPage extends Page {
  mount() {
    this.render(view());
  }
}

customElements.define("home-page", LandingPage);
