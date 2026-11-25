import { html, render } from "../core/html.js";
import { Component } from "../core/page.js";
import { navigate } from "../core/router.js";
import { notifications } from "../core/store.js";
import { markAllRead, markRead } from "../services/notifications.js";

// One unread notification. Game invites open the game; the others the
// sender's profile. System notifications (no sender) have no button.
const item = (notification) => {
  const sender = notification.sender || {};
  const isInvite = notification.ctx === "game_invite" || notification.type === "game_invite";
  let action = null;
  if (isInvite) {
    action = html`<button
      type="button"
      class="btn btn-dark btn-sm"
      data-game="${notification.game_id}"
    >
      Play Game
    </button>`;
  } else if (sender.uuid) {
    action = html`<button type="button" class="btn btn-dark btn-sm" data-profile="${sender.uuid}">
      View Profile
    </button>`;
  }
  return html`
    <div class="notification-list notification-list--unread" data-uuid="${notification.uuid ?? ""}">
      <div class="notification-list_img">
        <img
          src="${sender.avatar || ""}"
          alt="${sender.username ? `${sender.username}'s avatar` : ""}"
        />
      </div>
      <div class="notification-list_detail ms-3">
        <p class="mb-1">
          <b class="notification-list_username">${sender.username || ""}</b>
          <span class="notification-list_message">${notification.message}</span>
        </p>
        ${action}
      </div>
    </div>
  `;
};

const view = () => html`
  <div class="dropdown" id="notification-wrapper">
    <button
      class="nav-link dropdown-toggle notification-ui_icon me-4"
      id="navbarDropdown"
      role="button"
      data-bs-toggle="dropdown"
      aria-expanded="false"
      aria-label="Notifications"
    >
      <i class="fa fa-bell fs-5" aria-hidden="true"></i>
      <span class="counter" data-count>0</span>
    </button>
    <div class="dropdown-menu notification-ui_dd" aria-labelledby="navbarDropdown">
      <div class="notification-ui_dd-header">
        <h3 class="text-center">Notification</h3>
      </div>
      <div class="notification-ui_dd-content"></div>
      <div class="notification-ui_dd-footer">
        <button class="btn btn-success btn-block w-100 py-2" id="notification-btn">
          Mark all as read
        </button>
      </div>
    </div>
  </div>
`;

/**
 * The bell in the nav: follows the notification store. Only the counter,
 * the list and the button change, so an open dropdown stays open.
 */
class NotificationsMenu extends Component {
  mount() {
    this.render(view());
    this.counter = this.querySelector("[data-count]");
    this.list = this.querySelector(".notification-ui_dd-content");
    this.markAll = this.querySelector("#notification-btn");
    this.subscribe(notifications, (items) => this.update(items));
    this.on(this, "click", (event) => this.onClick(event));
  }

  update(items) {
    this.counter.textContent = items.length;
    this.markAll.disabled = items.length === 0;
    render(
      this.list,
      items.length
        ? html`${items.map(item)}`
        : html`<p class="text-center my-2">No new notifications</p>`,
    );
  }

  async onClick(event) {
    if (event.target.closest("#notification-btn")) {
      markAllRead();
      return;
    }
    const button = event.target.closest("[data-game], [data-profile]");
    if (!button) return;
    const uuid = button.closest(".notification-list").dataset.uuid;
    if (uuid) await markRead(uuid);
    navigate(
      button.dataset.game ? `/play/${button.dataset.game}` : `/friend/${button.dataset.profile}`,
    );
  }
}

customElements.define("notifications-menu", NotificationsMenu);
