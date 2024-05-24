// Pages Import
import { HomePage, NotFoundPage } from "./pages/index.js";

const routes = [
  {
    path: "/404",
    view: NotFoundPage,
    isProtected: false,
    page: "not-found-page",
  },
  { path: "/", view: HomePage, isProtected: false, page: "home-page" },
  // { path: '/login', isProtected: false, page: "login-view" },
  // { path: '/chat', view: ChatView, isProtected: false, page: "chat-view" },
  // { path: '/signup', view: SignupView, isProtected: false },
  // { path: '/friends', view: FriendsView, isProtected: false },
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
