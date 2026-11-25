import { toastOnError } from "../core/api.js";
import { navigate } from "../core/router.js";

/** Invite a friend to a game and open it. `client`: an API client. */
export const inviteToGame = async (client, friendId) => {
  const result = await client.post(`/api/game/invite_friend/${encodeURIComponent(friendId)}`);
  if (toastOnError(result)) navigate(`/play/${result.data.game.id}`);
};

/** A new game against the same opponent, then open it. */
export const playAgain = async (client, gameId) => {
  const result = await client.post(`/api/game/play_again/${encodeURIComponent(gameId)}`);
  if (toastOnError(result)) navigate(`/play/${result.data.game.id}`);
};
