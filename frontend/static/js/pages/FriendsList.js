import API from "../API/API.js";

class FriendsList extends HTMLElement {
  constructor() {
    super();
  }
  connectedCallback() {
    const template = document.getElementById("friends");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.API = new API();
    this.render();
  }

  async render() {
    try {
      this.friends = await this.API.getFriends();
      const friendsList = this.querySelector("#friends-list");
      friendsList.innerHTML = "";
      if (this.friends.length === 0) {
        const noFriends = document.createElement("p");
        noFriends.innerText = "No friends found";
        friendsList.appendChild(noFriends);
      }
      for (const user of this.friends) {
        const userElement = document.createElement("div");
        userElement.setAttribute("class", "contact");
        userElement.setAttribute("id", user.friend.username);
        userElement.innerHTML = `
            <li>
              <img class="avatar" src="${user.friend.profile.avatar}" alt="avatar"/>  
              <span>${user.friend.username}</span>
            </li>
        `;
        friendsList.appendChild(userElement);
      }
    } catch (error) {
      console.error("Error rendering friends:", error);
      this.querySelector("#friends-list").innerHTML = "Error loading friends";
    }
  }
}
customElements.define("friends-list", FriendsList);

export default FriendsList;
