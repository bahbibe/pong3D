import { navigateTo, BASE_URL } from "./router.js";
import { escapeHTML as esc } from "./escape.js";

export const hideToast = () => {
  document.querySelector(`#toast-wrapper .toast`).classList.remove("show");
  document.querySelector(`#toast-wrapper .toast`).classList.add("hide");
}

export const showToast = (isError, message, errors) => {
  const errorsEl = document.querySelector(`#toast-wrapper .toast`);
  if (isError) {
    errorsEl.classList.add("text-bg-danger");
    errorsEl.classList.remove("text-bg-success");
    document.querySelector(`#toast-wrapper .toast-header .me-auto`).innerHTML = "Error";
  } else {
    errorsEl.classList.remove("text-bg-danger");
    errorsEl.classList.add("text-bg-success");
    document.querySelector(`#toast-wrapper .toast-header .me-auto`).innerHTML = "Success";
  }
  const errorsContentEl = errorsEl.querySelector(".toast-body");
  if (errors && Object.keys(errors).length > 0) {
    // Error text can echo user input, so escape it.
    errorsContentEl.innerHTML = Object.keys(errors)
      .map((error) => `<p>${esc(error)}: ${esc(errors[error])}</p>`)
      .join("");
  } else {
    errorsContentEl.textContent = message || "Something went wrong!. Please try again later";
  }
  errorsEl.classList.add("show");
  errorsEl.classList.remove("hide");
  // setTimeout(() => {
  //   errorsEl.classList.remove("show");
  //   errorsEl.classList.add("hide");
  // }, 5000);
}


export const showOverlay = () => {
  const showOverlay = document.querySelector("#overlay");
  showOverlay.style.display = "block";
}

export const hideOverlay = () => {
  const showOverlay = document.querySelector("#overlay");
  setInterval(() => showOverlay.style.display = "none", 100);
}

export const renderNotifications = () => {
  const notifications = window.notifications || [];
  const notificationWrapper = document.getElementById("notification-wrapper");
  const notificationsEl = notificationWrapper.querySelector(".notification-ui_dd-content");
  const notificationCounter = notificationWrapper.querySelector("[data-count]");
  // notificationCounter.textContent = notifications.filter((notification) => !notification.is_read).length;
  notificationCounter.textContent = notifications.length;
  notificationWrapper.querySelector("#notification-btn").classList.remove("disabled");
  if (notifications.length === 0) {
    notificationsEl.innerHTML = `<p class="text-center my-2">No new notifications</p>`;
    notificationWrapper.querySelector("#notification-btn").classList.add("disabled");
    return
  };
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
    const isGameInvite = notification.ctx == "game_invite" || notification.type == "game_invite";

    img.src = notification.sender.avatar;
    username.textContent = notification.sender.username;
    if (isGameInvite) {
      btn.textContent = "Play Game";
      btn.dataset.game_id = notification.game_id;
    } else {
      btn.textContent = "View Profile";
      btn.dataset.id = notification.sender.uuid;
    }
    // btn.dataset.notification_id = notification.uuid;
    message.textContent = notification.message;
    notificationsEl.insertAdjacentHTML("beforeend", notif.outerHTML);
  });

  const buttonsList = notificationsEl.querySelectorAll(".notification-list button");
  buttonsList.forEach((btn) => {
    btn.addEventListener("click", () => {
      // markNotificationAsRead(btn.dataset.notification_id);
      if (btn.dataset.game_id) {
        console.log("Viewing game");
        navigateTo(`/play/${btn.dataset.game_id}`);
        return;
      }
      console.log("Viewing profile");
      navigateTo(`/friend/${btn.dataset.id}`);
    });
  });
}

// const markNotificationAsRead = async (notification_uuid) => {
//   try {
//     fetch(
//       `${BASE_URL}/api/auth/notifications/mark_as_read/${notification_uuid}/`,
//       {
//         method: "POST",
//         credentials: "include",
//       }
//     );
//   } catch (error) {
//     console.log(error);
//   }
// }