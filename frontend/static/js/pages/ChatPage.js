import { WebSock } from "../ws/ws.js";
import { AbstractPage } from "./AbstarctPage.js";
import { Friendships } from "../API/Friends.js";
import { User } from "../API/User.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.friendships = new Friendships();
    this.user = new User();
    this.renderProfile();
    this.renderFriends().then(() => {
      this.querySelectorAll(".DM").forEach((DM) => {
        DM.addEventListener("click", this.renderMessages.bind(this));
      });
    });
  }

  async renderFriends() {
    try {
      this.friends = await this.friendships.getFriends();
      for (const user of this.friends) {
        const userElement = document.createElement("div");
        userElement.setAttribute("class", "DM");
        userElement.setAttribute("id", user.friend.username);
        userElement.innerHTML = `
            <li>
              <img class="avatar" src="${user.friend.profile.avatar}" alt="avatar"/>  
              <span>${user.friend.username}</span>
            </li>
        `;
        this.querySelector("#chat-users-list").appendChild(userElement);
      }
    } catch (error) {
      console.error("Error rendering friends:", error);
    }
  }

  async renderMessages(e) {
    e.preventDefault();
    //! CSS
    this.querySelector(".messages-container").style.display = "block";
    this.querySelector("#chat-messages-list").innerHTML = "";
    //! CSS
    try {
      if (this.ws) {
        this.ws.close();
      }
      const uuid = this.friends.find(
        (friend) => friend.friend.username === e.currentTarget.id
      ).uuid;
      await this.friendships.getMessages(uuid).then((DMs) => {
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
      });
      this.ws = new WebSock(uuid);
      await this.ws.connect();
      this.querySelector("#chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = e.target.querySelector("input").value;
        if (message) {
          this.ws.send({ message });
        }
        e.target.reset();
      });
      await this.ws.receive().then((data) => {
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
      // await ws.close();
    } catch (error) {
      console.error("Error rendering DMs:", error);
    }
  }
  async renderProfile() {
    try {
      const profile = await this.user.getUser();
      this.user = profile;
      this.querySelector("#profile-username").textContent = profile.username;
      this.querySelector("#profile-avatar").src = profile.profile.avatar;
    } catch (error) {
      console.error("Error rendering profile:", error);
    }
  }
}

window.customElements.define("chat-page", ChatPage);
export { ChatPage };
