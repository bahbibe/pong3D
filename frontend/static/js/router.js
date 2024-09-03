// Pages Import
import { ChatPage, HomePage, NotFoundPage, LoginPage, ProfilePage, RankingPage, SettingsPage, Home } from "./pages/index.js";

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
  { path: "/profile", view: ProfilePage, isProtected: true, page: "user-profile" },
  { path: "/ranking", view: RankingPage, isProtected: true, page: "ranking-page" },
  { path: "/settings", view: SettingsPage, isProtected: true, page: "settings-page" },
  { path: "/home", view: Home, isProtected: true, page: "user-home" },
  { path: "/chat", view: ChatPage, isProtected: true, page: "chat-page" },
  {
    path: "/chat/:roomId",
    view: ChatPage,
    isProtected: true,
    page: "chat-page",
  },
];

const navigateTo = (url) => {
  history.pushState(null, null, url);
  router();
};

const getUser = async () => {
  const data = await fetch("http://localhost:8000/api/auth/me/", {
    credentials: "include",
  });
  const user = await data.json();
  if (user && user.success === true) {
    window.user = user;
    return true;
  }
  return false;
}

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
  console.log("User: ", isLoggedIn);
  console.log("from routing User: ", window.user);
  if (match.route.isProtected && !isLoggedIn) {
    navigateTo("/login");
    return;
  }
  else if (!match.route.isProtected && isLoggedIn) {
    navigateTo("/home");
    return;
  }

  const appEl = document.getElementById("app");
  appEl.innerHTML = "";
  const template = document.createElement(match.route.page);
  template.setAttribute("params", JSON.stringify(getParams(match)));
  appEl.appendChild(template);
};

export { router, navigateTo };
