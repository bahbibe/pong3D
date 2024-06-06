// Pages Import
import { ChatPage, HomePage, NotFoundPage, LoginPage } from "./pages/index.js";

const routes = [
  {
    path: "/404",
    view: NotFoundPage,
    isProtected: false,
    page: "not-found-page",
  },
  { path: "/", view: HomePage, isProtected: false, page: "home-page" },
  { path: "/login", view: HomePage, isProtected: false, page: "login-page" },
  { path: '/chat', view: ChatPage, isProtected: false, page: "chat-page", },
  { path: '/chat/:roomId', view: ChatPage, isProtected: false, page: "chat-page", },
  { path: '/login', view: LoginPage, isProtected: false, page: "login-page", },
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
      isMatched: location.pathname === route.path,
    };
  });

  let match = matches.find((match) => match.isMatched);

  // Check if the match is undefined (404)
  if (!match) match = { route: routes[0], isMatched: true };

  // check if the route is protected
  if (match.route.isProtected) {
    navigateTo("/login");
    return;
  }

  const appEl = document.getElementById("app");
  appEl.innerHTML = "";
  const template = document.createElement(match.route.page);
  appEl.appendChild(template);
};

export { router, navigateTo };
