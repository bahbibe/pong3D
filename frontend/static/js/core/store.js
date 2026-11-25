/**
 * A value that others can watch. set() replaces it (or takes a function of
 * the current value) and calls every subscriber. subscribe() returns an
 * unsubscribe function, and also stops when `signal` aborts.
 */
export const createStore = (initial) => {
  let value = initial;
  const subscribers = new Set();
  return {
    get: () => value,
    set(next) {
      value = typeof next === "function" ? next(value) : next;
      for (const fn of [...subscribers]) fn(value);
    },
    subscribe(fn, { signal } = {}) {
      subscribers.add(fn);
      const unsubscribe = () => subscribers.delete(fn);
      signal?.addEventListener("abort", unsubscribe, { once: true });
      return unsubscribe;
    },
  };
};

/** Unread notifications of the current user, oldest first. */
export const notifications = createStore([]);

/** Ids (as strings) of the users online now. */
export const presence = createStore(new Set());
