import { navigate as navigateTo } from "./core/router.js";
import { markRead } from "./services/notifications.js";

export { hideToast, showToast } from "./core/toast.js";

import { overlay } from "./core/overlay.js";

export const showOverlay = () => overlay.show();
export const hideOverlay = () => overlay.hide();

export const renderNotifications = () => {
  const notifications = window.notifications || [];
  const notificationWrapper = document.getElementById("notification-wrapper");
  const notificationsEl = notificationWrapper.querySelector(".notification-ui_dd-content");
  const notificationCounter = notificationWrapper.querySelector("[data-count]");
  notificationCounter.textContent = notifications.length;
  notificationWrapper.querySelector("#notification-btn").classList.remove("disabled");
  if (notifications.length === 0) {
    notificationsEl.innerHTML = `<p class="text-center my-2">No new notifications</p>`;
    notificationWrapper.querySelector("#notification-btn").classList.add("disabled");
    return;
  }
  notificationsEl.innerHTML = "";
  notifications.forEach((notification) => {
    const notif = document.createElement("div");
    notif.className = `notification-list ${notification.is_read ? "" : "notification-list--unread"}`;
    notif.innerHTML = `
      <div class="notification-list_img">
        <img src="" alt="user">
      </div>
      <div class="notification-list_detail ms-3">
        <p class="mb-1"><b class="notification-list_username"></b> <span class="notification-list_message"></span></p>
        <button type="button" class="btn btn-dark btn-sm">View profile</button>
      </div>
    `;
    const img = notif.querySelector(".notification-list_img img");
    const username = notif.querySelector(".notification-list_username");
    const message = notif.querySelector(".notification-list_message");
    const btn = notif.querySelector("button");
    const isGameInvite = notification.ctx === "game_invite" || notification.type === "game_invite";

    // System notifications have no sender.
    const sender = notification.sender || {};
    img.src = sender.avatar || "";
    img.alt = sender.username ? `${sender.username}'s avatar` : "";
    username.textContent = sender.username || "";
    if (isGameInvite) {
      btn.textContent = "Play Game";
      btn.dataset.game_id = notification.game_id;
    } else if (sender.uuid) {
      btn.textContent = "View Profile";
      btn.dataset.id = sender.uuid;
    } else {
      btn.remove();
    }
    if (notification.uuid) notif.dataset.uuid = notification.uuid;
    message.textContent = notification.message;
    notificationsEl.insertAdjacentHTML("beforeend", notif.outerHTML);
  });

  const buttonsList = notificationsEl.querySelectorAll(".notification-list button");
  buttonsList.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const uuid = btn.closest(".notification-list")?.dataset.uuid;
      if (uuid) await markRead(uuid);
      if (btn.dataset.game_id) {
        navigateTo(`/play/${btn.dataset.game_id}`);
        return;
      }
      navigateTo(`/friend/${btn.dataset.id}`);
    });
  });
};
