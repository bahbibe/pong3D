import { WebSock } from "../ws/ws.js";
import { AbstractPage } from "./AbstarctPage.js";
import { friends } from "../API/friends.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.friends = new friends();
    this.renderFriends().then(() => {
      this.querySelectorAll(".DM").forEach((DM) => {
        DM.addEventListener("click", this.renderDM.bind(this));
      });
    });
  }

  async renderFriends() {
    try {
      const friends = await this.friends.getFriends();
      for (const user of friends) {
        const userElement = document.createElement("div");
        userElement.setAttribute("class", "DM");
        userElement.setAttribute("id", user.friend.username);
        userElement.innerHTML = `
            <li>
              <img class="avatar "src="${user.friend.profile.avatar}" alt="avatar"/>  
              <span>${user.friend.username}</span>
            </li>
        `;
        this.querySelector("#chat-users-list").appendChild(userElement);
      }
    } catch (error) {
      console.error("Error rendering friends:", error);
    }
  }

  async renderDM(e) {
    e.preventDefault();
    try {
      const ws = new WebSock(e.currentTarget.id);
      await ws.connect();
      this.querySelector(".messages-container").style.display = "block";
      this.querySelector("#chat-messages-list").innerHTML = "";
      const DMs = await this.friends.getDMs(e.currentTarget.id);
      console.log(DMs);
      if (DMs.length === 0) {
        const DMElement = document.createElement("div");
        DMElement.setAttribute("class", "msg");
        DMElement.innerHTML = `
          <li>
            <span>No messages yet.</span>
          </li>
        `;
        this.querySelector("#chat-messages-list").appendChild(DMElement);
      } else {
        for (const DM of DMs) {
          const DMElement = document.createElement("div");
          DMElement.setAttribute("class", "msg");
          DMElement.innerHTML = `
          <li>
            <span>${DM.content}</span>
            <span>${new Date(DM.timestamp).toLocaleString()}</span>
          </li>
        `;
          this.querySelector("#chat-messages-list").appendChild(DMElement);
        }
      }
      this.querySelector("#chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = e.target.querySelector("input").value;
        if (message) {
          ws.send({ message });
        }
        e.target.reset();
      });
      await ws.receive().then((data) => {
        const message = JSON.parse(data);
        const DMElement = document.createElement("div");
        DMElement.setAttribute("class", "msg");
        DMElement.innerHTML = `
          <li>
            <span>${message.message}</span>
            <span>${new Date().toLocaleString()}</span>
          </li>
        `;
        this.querySelector("#chat-messages-list").appendChild(DMElement);
      });
    } catch (error) {
      console.error("Error rendering DMs:", error);
      // ws.close();
    }
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
