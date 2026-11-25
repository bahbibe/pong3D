import { toastOnError } from "../core/api.js";
import { html, render } from "../core/html.js";
import { Component } from "../core/page.js";
import { navigate } from "../core/router.js";
import { session } from "../core/session.js";
import { presence } from "../core/store.js";
import { inviteToGame } from "../services/game.js";

// Close code of the chat socket when the session is gone.
const CLOSE_UNAUTHORIZED = 4001;

const view = (friend) => html`
  <div class="chat-container no-scroll p-2 d-flex flex-column h-100">
    <div class="msg-head mb-3 p-2 d-flex gap-2">
      <div class="d-flex align-items-center">
        <img
          src="${friend.profile.avatar}"
          class="d-block img-cover img-fluid rounded-circle h-100"
          alt="avatar"
        />
      </div>
      <div class="chat-info d-flex flex-column flex-grow-1 justify-content-center">
        <a href="/friend/${friend.profile.uuid}" data-link>
          <span class="fs-5">${friend.username}</span>
        </a>
        <span class="stat opacity-75">
          <i class="fa-solid fa-circle"></i> <span class="friend-status">Offline</span>
        </span>
      </div>
      <button type="button" class="btn challenge">
        <span class="d-none d-md-block">Challenge</span>
        <i class="fa-solid fa-gamepad fs-2 d-md-none" aria-label="Challenge"></i>
      </button>
    </div>
    <div class="msg-box no-scroll p-2 flex-grow-1"></div>
    <form class="input-group">
      <div class="send w-100 d-flex justify-content-around align-items-center mt-2">
        <input
          type="text"
          class="send-input me-0 h-100"
          placeholder="  Type a message"
          aria-label="Type a message"
        />
        <button class="send-icon btn h-100" type="submit" aria-label="Send">
          <i class="fs-3 fa-solid fa-paper-plane"></i>
        </button>
      </div>
    </form>
  </div>
`;

const message = (item) => {
  const mine = item.author === session.user.username;
  return html`<div class="${mine ? "msg-sent" : "msg-received"}"><p>${item.content}</p></div>`;
};

const empty = () => html`
  <div id="empty" class="d-flex justify-content-center h-100 align-items-center">
    <div class="d-flex flex-column gap-5 text-center">
      <span class="fs-2 fw-bold"> Hello !! </span>
      <span> <i class="fa-solid fa-hand-sparkles fa-bounce fs-1"></i> </span>
    </div>
  </div>
`;

/** The conversation with one friend. Set `friendship` ({uuid, friend}) before adding it. */
class ChatBox extends Component {
  async mount() {
    const { friend, uuid } = this.friendship;
    this.render(view(friend));
    this.messages = this.querySelector(".msg-box");
    this.subscribe(presence, (online) => this.showStatus(online.has(String(friend.id))));
    this.on(this.querySelector(".challenge"), "click", () => inviteToGame(this.api, friend.id));
    this.on(this.querySelector("form"), "submit", (event) => {
      event.preventDefault();
      this.send();
    });

    const history = await this.api.get(`/api/chat/messages/${encodeURIComponent(uuid)}/`);
    if (!toastOnError(history)) return;
    render(
      this.messages,
      history.data.messages.length ? html`${history.data.messages.map(message)}` : empty(),
    );
    this.scrollDown();
    this.connection = this.socket(`/ws/chat/${encodeURIComponent(uuid)}/`, {
      onMessage: (message) => this.add(message),
      onClose: (event) => {
        if (event.code !== CLOSE_UNAUTHORIZED) return;
        session.clear();
        navigate("/login");
      },
    });
  }

  add(item) {
    // The "Hello !!" placeholder goes once there is a message.
    this.messages.querySelector("#empty")?.remove();
    this.messages.insertAdjacentHTML("beforeend", String(message(item)));
    this.scrollDown();
  }

  send() {
    const input = this.querySelector(".send-input");
    const content = input.value;
    if (content.trim() === "" || this.connection?.readyState !== WebSocket.OPEN) return;
    // The server sets the author from the session: only the text is sent.
    this.connection.send(JSON.stringify({ content }));
    input.value = "";
  }

  showStatus(online) {
    const stat = this.querySelector(".stat");
    stat.classList.toggle("online", online);
    stat.querySelector(".friend-status").textContent = online ? "Online" : "Offline";
  }

  scrollDown() {
    this.messages.scrollTop = this.messages.scrollHeight;
  }
}

customElements.define("chat-box", ChatBox);
