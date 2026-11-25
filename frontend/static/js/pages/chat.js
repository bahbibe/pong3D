import "../components/chat-box.js";
import "../components/friends-list.js";
import { html } from "../core/html.js";
import { Page } from "../core/page.js";

const view = () => html`

  <main-nav></main-nav>
  <div class=" chat-container p-3 container-md d-flex ">
    <div class="side d-flex flex-column">
      <div class=" chat-heading p-3 me-2 mb-2 blur">
        <div class="px-2 d-flex gap-2 justify-content-center justify-content-md-start align-items-center ">
          <i class=" fa-solid fa-user-group fs-3"> </i>
          <span class="d-none d-md-flex fs-2"> Contacts</span>
        </div>
      </div>
      <div class="friends-list  blur py-1 me-2"><friends-list></friends-list></div>
    </div>
    <div class="chat-box blur col-10 col-md-8 p-0">
      <div class=" d-flex justify-content-center align-items-center h-100">
        <img src="/static/asset/images/no-message.png" class=" w-25 opacity-25" alt="chat image">
      </div>
    </div>
  </div>
  </div>
`;

/** Contacts on the left; the conversation with the chosen one on the right. */
class ChatPage extends Page {
  mount() {
    this.render(view());
    this.on(this, "contact-selected", (event) => {
      const box = document.createElement("chat-box");
      box.friendship = event.detail;
      this.querySelector(".chat-box").replaceChildren(box);
    });
  }
}

customElements.define("chat-page", ChatPage);
