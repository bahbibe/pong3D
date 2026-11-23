// Pages Import
import {
  ChatPage,
  HomePage,
  NotFoundPage,
  LoginPage,
  ProfilePage,
  RankingPage,
  SettingsPage,
  Home,
  SearchPage,
  FriendPage,
  SetupPage,
  TwoFaPage,
  GamePage,
  MatchmakingPage,
  blockedFriendsPage,
} from "./pages/index.js";
import { FriendsStatus } from "./ws/FriendsStatus.js";
import { Notifications } from "./ws/NotificationsSockets.js";
import { TournamentDisplayPage } from "./pages/TournamentDisplayPage.js";
import { ScorePage } from "./pages/ScorePage.js";

// The app is served by nginx on the same origin as the API and WebSockets
// (https://localhost:1337). Relative URLs keep requests on that origin, so
// TLS is used and no CORS is needed.
export const BASE_URL = "";
export const WSS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;

const pathToRegex = (path) =>
  new RegExp("^" + path.replace(/\//g, "\\/").replace(/:\w+/g, "(.+)") + "$");

const getParams = (match) => {
  const values = match.result.slice(1);
  const keys = Array.from(match.route.path.matchAll(/:(\w+)/g)).map(
    (result) => result[1]
  );

  return Object.fromEntries(keys.map((key, i) => [key, values[i]]));
};

const routes = [
  {
    path: "/404",
    view: NotFoundPage,
    isProtected: false,
    page: "not-found-page",
  },
  { path: "/", view: HomePage, isProtected: false, page: "home-page" },
  { path: "/login", view: LoginPage, isProtected: false, page: "login-page" },
  { path: "/twofa", view: TwoFaPage, isProtected: true, page: "two-fa-page" },
  {
    path: "/profile",
    view: ProfilePage,
    isProtected: true,
    page: "user-profile",
  },
  {
    path: "/ranking",
    view: RankingPage,
    isProtected: true,
    page: "ranking-page",
  },
  {
    path: "/settings",
    view: SettingsPage,
    isProtected: true,
    page: "settings-page",
  },
  { path: "/search", view: SearchPage, isProtected: true, page: "search-page" },
  { path: "/home", view: Home, isProtected: true, page: "user-home" },
  { path: "/chat", view: ChatPage, isProtected: true, page: "chat-page" },
  {
    path: "/friend/:uuid",
    view: FriendPage,
    isProtected: true,
    page: "friend-page",
  },
  {
    path: "/blocked",
    view: FriendPage,
    isProtected: true,
    page: "blocked-page",
  },
  { path: "/play", view: GamePage, isProtected: true, page: "game-page" },
  {
    path: "/matchmaking",
    view: MatchmakingPage,
    isProtected: true,
    page: "matchmaking-page",
  },
  {
    path: "/play/:tournament_id/:game_id",
    view: GamePage,
    isProtected: true,
    page: "game-page",
  },
  {
    path: "/play/:game_id",
    view: GamePage,
    isProtected: true,
    page: "game-page",
  },
  {
    path: "/tournament/:tournament_id",
    view: TournamentDisplayPage,
    isProtected: true,
    page: "tournament-display-page",
  },
  {
    path: "/score/:game_id",
    view: ScorePage,
    isProtected: true,
    page: "score-page",
  },
  {
    path: "/tournament",
    view: ScorePage,
    isProtected: true,
    page: "tour-page",
  },
  { path: "/join", view: ScorePage, isProtected: true, page: "join-page" },
  {
    path: "/chat/:roomId",
    view: ChatPage,
    isProtected: true,
    page: "chat-page",
  },
  {
    path: "/setup",
    view: SetupPage,
    isProtected: true,
    page: "setup-page",
  },
];

const navigateTo = (url) => {
  history.pushState(null, null, url);
  router();
};

const getUser = async () => {
  let response = null;
  try {
    const data = await fetch(`${BASE_URL}/api/auth/me/`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
    response = await data.json();
  } catch (error) {
    // Network error or non-JSON answer: treat as logged out instead of
    // leaving a blank page.
    console.error("Could not load the current user:", error);
    return false;
  }
  if (response && response.success === true) {
    window.user = response.data.user;
    window.notifications = response.data.notifications;
    if (
      response.data.is_tfa_verified === false &&
      window.path !== "/twofa" &&
      window.path !== "/setup"
    ) {
      navigateTo("/twofa");
      return true;
    }
    FriendsStatus();
    Notifications();
    return true;
  }
  return false;
};

const router = async () => {
  // check potential matching routes
  const matches = routes.map((route) => {
    return {
      route: route,
      result: location.pathname.match(pathToRegex(route.path)),
      isMatched: location.pathname.match(pathToRegex(route.path))
        ? true
        : false,
    };
  });
  let match = matches.find((match) => match.isMatched);

  // Check if the match is undefined (404)
  if (!match)
    match = { route: routes[0], isMatched: true, result: [location.pathname] };
  window.path = match.route.path;

  // check if the route is protected
  let isLoggedIn = await getUser();
  if (match.route.isProtected && !isLoggedIn) {
    navigateTo("/login");
    return;
  } else if (!match.route.isProtected && isLoggedIn) {
    navigateTo("/home");
    return;
  } else if (match.route.isProtected && isLoggedIn) {
    if (match.route.path === "/setup") {
      if (window.user.profile.is_setup) {
        navigateTo("/home");
        return;
      }
    }

    if (!window.user.profile.is_setup && match.route.path !== "/setup") {
      navigateTo("/setup");
      return;
    }
  }

  const appEl = document.getElementById("app");
  appEl.innerHTML = "";
  const template = document.createElement(match.route.page);
  template.setAttribute("params", JSON.stringify(getParams(match)));
  appEl.appendChild(template);
};

export { router, navigateTo };
