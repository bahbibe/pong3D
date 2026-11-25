// Entry point: the router and in-app links.
import { navigate, router } from "./core/router.js";

window.addEventListener("popstate", () => router());

// Links with data-link change the page without a reload. Ctrl/cmd/shift
// clicks, middle clicks and target=_blank keep the browser's behavior.
document.addEventListener("click", (event) => {
  // closest(): the click may land on an icon or span inside the link.
  const link = event.target.closest("[data-link]");
  if (!link || event.defaultPrevented || event.button !== 0) return;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  if (link.target === "_blank") return;
  event.preventDefault();
  navigate(link.href);
});

router();
