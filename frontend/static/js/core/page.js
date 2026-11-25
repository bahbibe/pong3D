import { api } from "./api.js";
import { WSS_URL } from "./config.js";
import { render } from "./html.js";
import { openReconnectingSocket } from "./sockets.js";

/**
 * Base of every custom element. mount() runs when it is added to the page,
 * unmount() when it is removed. Everything set up through the helpers below
 * is undone on removal: listeners, requests in flight, sockets, timers and
 * store subscriptions. A late answer never writes into a page that is gone.
 */
export class Component extends HTMLElement {
  connectedCallback() {
    this.lifecycle = new AbortController();
    this.mount?.();
  }

  disconnectedCallback() {
    this.lifecycle?.abort();
    this.unmount?.();
  }

  get signal() {
    return this.lifecycle.signal;
  }

  /** addEventListener, removed on unmount. */
  on(target, type, listener, options = {}) {
    target.addEventListener(type, listener, { ...options, signal: this.signal });
  }

  /** The API client; requests still running on unmount are cancelled. */
  get api() {
    return api.withSignal(this.signal);
  }

  /**
   * A WebSocket on `path` (e.g. "/ws/chat/<uuid>/"), closed on unmount.
   * reconnect: true reopens it after a drop (see sockets.js).
   * Handlers: onOpen, onMessage(data parsed from JSON), onClose(event).
   */
  socket(path, { onOpen, onMessage, onClose } = {}, { reconnect = false } = {}) {
    const parse = (event) => onMessage?.(JSON.parse(event.data));
    if (reconnect) {
      const handle = openReconnectingSocket(path, { onOpen, onMessage: parse });
      this.signal.addEventListener("abort", () => handle.close(), { once: true });
      return handle;
    }
    const socket = new WebSocket(`${WSS_URL}${path}`);
    if (onOpen) socket.addEventListener("open", onOpen);
    socket.addEventListener("message", parse);
    if (onClose) socket.addEventListener("close", onClose);
    this.signal.addEventListener("abort", () => socket.close(), { once: true });
    return socket;
  }

  /** setTimeout, cleared on unmount. */
  timeout(fn, ms) {
    const id = setTimeout(fn, ms);
    this.signal.addEventListener("abort", () => clearTimeout(id), { once: true });
    return id;
  }

  /** Follow a store: fn(value) now and on every change, until unmount. */
  subscribe(store, fn) {
    fn(store.get());
    return store.subscribe(fn, { signal: this.signal });
  }

  /** Replace this element's content with a html`` template. */
  render(template) {
    return render(this, template);
  }
}

/**
 * A routed page. The router sets `route` ({params, query}) before adding
 * it; static `title` names the browser tab.
 */
export class Page extends Component {
  static title = "";

  get params() {
    return this.route?.params ?? {};
  }

  get query() {
    return this.route?.query ?? new URLSearchParams();
  }
}
