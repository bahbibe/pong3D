import { router, navigateTo } from "./router.js";

// the forward and prev history
window.addEventListener("popstate", router);

document.addEventListener("DOMContentLoaded", async () => {
  // check for any link with (data-link) attr
  document.body.addEventListener("click", (event) => {
    if (event.target.matches("[data-link]")) {
      event.preventDefault();
      navigateTo(event.target.href);
    }
  });

  router();
});
