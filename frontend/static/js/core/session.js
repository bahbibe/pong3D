import * as notificationService from "../services/notifications.js";
import * as presenceService from "../services/presence.js";
import { api } from "./api.js";
import { notifications } from "./store.js";

/**
 * The logged-in user, loaded once from /api/auth/me/ and kept until
 * something changes it (login, 2FA, setup, logout, a 401). The router calls
 * load() when it needs a fresh answer. The status and notification sockets
 * run while a user is fully logged in (2FA done).
 */
let user = null;
let tfaPending = false;
let loaded = false;

const startServices = () => {
  presenceService.start();
  notificationService.start();
};

const stopServices = () => {
  presenceService.stop();
  notificationService.stop();
};

export const session = {
  get user() {
    return user;
  },
  get loaded() {
    return loaded;
  },
  /** Logged in, 2FA code still to enter. */
  get tfaPending() {
    return tfaPending;
  },

  async load() {
    const result = await api.get("/api/auth/me/", { auth: false });
    loaded = true;
    // The 2FA-pending answer is a 200 with the user and is_tfa_verified: false.
    if (result.data?.user) {
      user = result.data.user;
      tfaPending = result.data.is_tfa_verified === false;
      if (tfaPending) {
        stopServices();
      } else {
        notifications.set(result.data.notifications ?? []);
        startServices();
      }
    } else {
      session.clear();
    }
    return session;
  },

  /** New data for the current user (e.g. the answer of a settings update). */
  setUser(next) {
    user = next;
  },

  /** Forget the user (logout, or the server said the session is gone). */
  clear() {
    user = null;
    tfaPending = false;
    stopServices();
    notifications.set([]);
  },
};
