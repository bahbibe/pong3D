import { toastOnError } from "../core/api.js";
import { html } from "../core/html.js";
import { Component } from "../core/page.js";

const contact = (item) => html`
  <div class="contact p-2 mx-1 d-flex gap-2" data-id="${item.friend.id}">
    <div class="d-flex align-items-center">
      <img
        src="${item.friend.profile.avatar}"
        class="d-block img-cover img-fluid rounded-circle"
        alt=""
      />
    </div>
    <div class="d-none d-md-block col-md-9 col-lg-10">
      <div class="last-msg d-flex flex-column h-100 justify-content-center">
        <p class="m-0 fs-5">${item.friend.username}</p>
      </div>
    </div>
  </div>
`;

/**
 * The friends you can chat with. Clicking one fires "contact-selected"
 * (bubbles) with the friendship ({uuid, friend}) as detail.
 */
class FriendsList extends Component {
  async mount() {
    this.friends = [];
    this.on(this, "click", (event) => this.select(event.target.closest(".contact")));
    const result = await this.api.get("/api/friends/");
    if (!toastOnError(result)) return;
    this.friends = result.data;
    this.render(this.friends.length ? html`${this.friends.map(contact)}` : html`No friends yet`);
  }

  select(element) {
    if (!element) return;
    this.querySelector(".contact.active")?.classList.remove("active");
    element.classList.add("active");
    const friendship = this.friends.find((item) => String(item.friend.id) === element.dataset.id);
    this.dispatchEvent(new CustomEvent("contact-selected", { detail: friendship, bubbles: true }));
  }
}

customElements.define("friends-list", FriendsList);
