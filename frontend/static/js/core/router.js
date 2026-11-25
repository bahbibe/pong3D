// Page modules define their custom elements when imported. Routes render
// them by tag name.
import "../pages/index.js";
import { setAuthHandler } from "./api.js";
import { session } from "./session.js";

/**
 * access:
 *   public  logged-out pages (logged in: sent to /home)
 *   user    logged in, 2FA done, profile set up
 *   any     everyone (the not-found page)
 * /twofa and /setup are the steps a logged-in user may still have to do;
 * the guard sends them there.
 */
const ROUTES = [
  { path: "/", tag: "home-page", access: "public" },
  { path: "/login", tag: "login-page", access: "public", title: "Login" },
  { path: "/twofa", tag: "two-fa-page", access: "user", title: "Two-factor code" },
  { path: "/setup", tag: "setup-page", access: "user", title: "Set up your profile" },
  { path: "/home", tag: "user-home", access: "user", title: "Home" },
  { path: "/profile", tag: "user-profile", access: "user", title: "Profile" },
  { path: "/ranking", tag: "ranking-page", access: "user", title: "Ranking" },
  { path: "/settings", tag: "settings-page", access: "user", title: "Settings" },
  { path: "/search", tag: "search-page", access: "user", title: "Search" },
  { path: "/chat", tag: "chat-page", access: "user", title: "Chat" },
  { path: "/chat/:roomId", tag: "chat-page", access: "user", title: "Chat" },
  { path: "/friend/:uuid", tag: "friend-page", access: "user", title: "Player" },
  { path: "/matchmaking", tag: "matchmaking-page", access: "user", title: "Matchmaking" },
  { path: "/play", tag: "game-page", access: "user", title: "Game" },
  { path: "/play/:game_id", tag: "game-page", access: "user", title: "Game" },
  { path: "/play/:tournament_id/:game_id", tag: "game-page", access: "user", title: "Game" },
  { path: "/score/:game_id", tag: "score-page", access: "user", title: "Score" },
  { path: "/tournament", tag: "tour-page", access: "user", title: "Tournament" },
  {
    path: "/tournament/:tournament_id",
    tag: "tournament-display-page",
    access: "user",
    title: "Tournament",
  },
  { path: "/join", tag: "join-page", access: "user", title: "Join a tournament" },
  { path: "/404", tag: "not-found-page", access: "any", title: "Not found" },
].map((route) => ({
  ...route,
  keys: [...route.path.matchAll(/:(\w+)/g)].map((m) => m[1]),
  regex: new RegExp(`^${route.path.replace(/:\w+/g, "([^/]+)")}/?$`),
}));

const NOT_FOUND = ROUTES.find((route) => route.path === "/404");

const match = (pathname) => {
  for (const route of ROUTES) {
    const found = pathname.match(route.regex);
    if (!found) continue;
    try {
      const values = found.slice(1).map(decodeURIComponent);
      return { route, params: Object.fromEntries(route.keys.map((key, i) => [key, values[i]])) };
    } catch {
      break; // malformed %-escape: not found
    }
  }
  return { route: NOT_FOUND, params: {} };
};

/** Where the guard sends this session for this route, or null to stay. */
const redirectFor = (route) => {
  const user = session.user;
  if (!user) return route.access === "user" ? "/login" : null;
  if (session.tfaPending) return route.path === "/twofa" ? null : "/twofa";
  if (!user.profile.is_setup) return route.path === "/setup" ? null : "/setup";
  if (route.access === "public" || route.path === "/twofa" || route.path === "/setup")
    return "/home";
  return null;
};

let current = 0;

export const router = async ({ scroll = false } = {}) => {
  const navigation = ++current;
  const { route, params } = match(location.pathname);

  // The cached session answers most navigations without a request. When it
  // says to go elsewhere, ask the server again first: logging in, entering
  // the 2FA code or finishing the setup changed it there.
  let fresh = false;
  if (!session.loaded) {
    await session.load();
    fresh = true;
  }
  let target = redirectFor(route);
  if (target && !fresh) {
    await session.load();
    target = redirectFor(route);
  }
  // A newer navigation started while we waited: it renders, not us.
  if (navigation !== current) return;
  if (target) {
    navigate(target, { replace: true });
    return;
  }

  const page = document.createElement(route.tag);
  page.route = { params, query: new URLSearchParams(location.search) };
  document.getElementById("app").replaceChildren(page);
  document.title = route.title ? `${route.title} · PONG` : "PONG";
  if (scroll) window.scrollTo(0, 0);
};

/** Go to `url` inside the app. replace: true does not add a history entry. */
export const navigate = (url, { replace = false } = {}) => {
  if (replace) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  return router({ scroll: !replace });
};

// An API call found the session gone (401) or waiting for the 2FA code:
// update the session and let the guard pick the page.
setAuthHandler(async (problem) => {
  if (problem === "unauthorized") session.clear();
  else await session.load();
  router();
});
