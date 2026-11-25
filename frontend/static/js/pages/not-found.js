import { html } from "../core/html.js";
import { Page } from "../core/page.js";

class NotFoundPage extends Page {
  mount() {
    this.render(html`
      <section class="p-1">
        <div
          class="container vt323-regular d-flex flex-column  justify-content-center text-center text-capitalize"
          style="height: 100dvh; width: 100vw;"
        >
          <h1 class="display-1 fw-bolder">404 Not Found</h1>
          <p class="display-6">Sorry, the page you are looking for does not exist.</p>
        </div>
      </section>
    `);
  }
}

customElements.define("not-found-page", NotFoundPage);
