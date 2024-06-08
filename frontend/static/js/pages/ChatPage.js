import { WebSockets } from "../ws/ws.js";
import { AbstractPage } from "./AbstarctPage.js";

class ChatPage extends AbstractPage {
  constructor() {
    super();
  }
  connectedCallback() {
    console.log("Room Id ==> ", this.params.roomId);
    const template = document.getElementById("chat-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    // this.renderFriends();
    // const DMs = this.querySelectorAll(".DM");
    // DMs.forEach(DM => {
    //   DM.addEventListener('click', this.renderDM);
    //  });
    // this.renderDM();
    this.fetchDMs();
  }
  async fetchfriends() {
    try {
      const response = await fetch("http://localhost:8000/api/friends/", {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });
      if (!response.ok) {
        alert("Unauthorized access. Please login.");
        window.location.href = "/login";
        throw new Error(`API request failed with status: ${response.status}`);
      }
      const res = await response.json();
      this.friends = res.data;
    } catch (error) {
      console.error("Error Loading friends:", error);
    }
  }

  async fetchDMs() {
    try {
      const response = await fetch("http://localhost:8000/chat/messages", {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });
      // if (!response.ok) {
      //   alert("Unauthorized access. Please login.");
      //   window.location.href = "/login";
      //   throw new Error(`API request failed with status: ${response.status}`);
      // }
      console.log("response ==> ", response);
      const res = await response.json();
      this.DMs = res.data;
      console.log("DMs ==> ", this.DMs);
    } catch (error) {
      console.error("Error Loading DMs:", error);
    }
  }

  async renderFriends() {
    try {
      await this.fetchfriends();
      const usersList = this.querySelector("#chat-users-list");
      for (const user of this.friends) {
        const userElement = document.createElement("li");
        userElement.innerHTML = `
          <li>
          <a  class="DM" href="/chat/${user.friend.username}">
            <img src="${user.friend.profile.avatar}" alt="avatar" width="50" height="50"/>  
            <span>${user.friend.username}</span>
            </a>
            <button>Challenge</button>
          </li>
        `;
        usersList.appendChild(userElement);
      }
    } catch (error) {
      console.error("Error rendering friends:", error);
    }
  }
  async renderDM(e) {
    e.preventDefault();
      try {
        await this.fetchDMs();
        const DMsList = this.querySelector("#chat-DMs-list");
        for (const DM of this.DMs) {
          const DMElement = document.createElement("li");
          DMElement.innerHTML = `
            <li>
              <span>${DM.friend.username}</span>
              <span>${DM.message}</span>
            </li>
          `;
          DMsList.appendChild(DMElement);
        }
      }
      catch (error) {
        console.error("Error rendering DMs:", error);
      }
    }
  }

window.customElements.define("chat-page", ChatPage);

export { ChatPage };
