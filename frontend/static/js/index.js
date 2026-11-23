import { router, navigateTo } from "./router.js";

// the forward and prev history
window.addEventListener("popstate", router);

document.addEventListener("DOMContentLoaded", async () => {
  // check for any link with (data-link) attr
  document.body.addEventListener("click", (event) => {
    // closest(): the click may land on an icon or span inside the link.
    const link = event.target.closest("[data-link]");
    if (link) {
      event.preventDefault();
      navigateTo(link.href);
    }
  });

  router();
});
