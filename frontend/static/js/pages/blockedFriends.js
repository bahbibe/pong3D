import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class blockedFriendsPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("blocked-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.container = document.querySelector("#search-container");
    
    this.renderBlockedFriends();
  }
  async renderBlockedFriends() {
    try {
      const response = await fetch('http://localhost:8000/api/friends/blocked/', { credentials: "include",});
      const data = await response.json();
      const users = data.data;

      for (const user of users) {

            this.container.innerHTML += `
            <div class="secondary-bg box-sh-1 p-2 text-center rounded  me-2" style="width: 160px; height: 190px;">
                      <div class="img ">
                        <img class="img-fluid rounded rounded-circle" src="${user.friend.profile.avatar}" alt="" width="100" height="100">
                      </div>
                      <div class="my-1">
                        <span class="font-monospace fw-bold">${user.friend.username} </span>
                      </div>
                      <button class="btn btn-block  fw-bolder shadow" id="unblock"'>unblock</button>
            </div>
            `
      }
    } catch (error) { console.log(error); }

  }
}


window.customElements.define("blocked-page", blockedFriendsPage);

export { blockedFriendsPage}