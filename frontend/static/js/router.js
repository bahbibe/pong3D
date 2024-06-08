// Pages Import
import { ChatPage, HomePage, NotFoundPage, LoginPage } from "./pages/index.js";

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
  { path: "/chat", view: ChatPage, isProtected: false, page: "chat-page" },
  {
    path: "/chat/:roomId",
    view: ChatPage,
    isProtected: false,
    page: "chat-page",
  },
];

const navigateTo = (url) => {
  history.pushState(null, null, url);
  router();
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

  // check if the route is protected
  if (match.route.isProtected) {
    navigateTo("/login");
    return;
  }

  const appEl = document.getElementById("app");
  appEl.innerHTML = "";
  const template = document.createElement(match.route.page);
  template.setAttribute("params", JSON.stringify(getParams(match)));
  appEl.appendChild(template);
};

export { router, navigateTo };
