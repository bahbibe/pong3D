import { navigateTo, BASE_URL } from "../router.js";

/**
 * Small wrapper around the backend API. Every method resolves to the
 * response's `data` field, or to undefined when the request fails (the
 * error is logged), which is what the pages expect.
 */
class API {
  async request(method, path, label) {
    try {
      const response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers: { "content-type": "application/json" },
        credentials: "include",
      });
      if (!response.ok) throw new Error(`API request failed with status: ${response.status}`);
      const body = await response.json();
      return body.data;
    } catch (error) {
      console.error(`Error ${label}:`, error);
      return undefined;
    }
  }

  async getFriends() {
    return this.request("GET", "/api/friends/", "loading friends");
  }

  async getMessages(uuid) {
    const data = await this.request("GET", `/api/chat/messages/${uuid}/`, "loading DMs");
    return data?.messages;
  }

  async getUser() {
    return this.request("GET", "/api/auth/me/", "loading profile");
  }

  async getTournaments() {
    return this.request("GET", "/api/game/get_tournaments/", "loading tournaments");
  }

  async getTournamentGames(tournamentId) {
    return this.request(
      "GET", `/api/game/get_tournament_games/${tournamentId}`, "loading tournament games"
    );
  }

  async create_tournament() {
    return this.request("POST", "/api/game/create_tournament/", "creating tournament");
  }

  async get_game(gameId) {
    return this.request("GET", `/api/game/get_game/${gameId}`, "loading game");
  }

  // invite_friend and play_again open the new game when it is created.
  async invite_friend(friendId) {
    const data = await this.request("POST", `/api/game/invite_friend/${friendId}`, "inviting friend");
    if (data?.game) navigateTo(`/play/${data.game.id}`);
  }

  async play_again(gameId) {
    const data = await this.request("POST", `/api/game/play_again/${gameId}`, "starting new game");
    if (data?.game) navigateTo(`/play/${data.game.id}`);
  }
}

export { API };
