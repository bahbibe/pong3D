import API from "../API/API.js";

class Friends extends HTMLElement {
  constructor() {
    super();
    this.API = new API();
  }
  connectedCallback() {
    const template = document.getElementById("friends");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
  }
  async render() {
    try {
      this.friends = await this.API.getFriends();
      this.friends.forEach((item) => {
        this.querySelector("#friends-list").appendChild(
          this.createFriendElement(item)
        );
      });
      if (friends.length === 0) {
        const noFriends = document.createElement("p");
        noFriends.innerText = "No friends found";
        this.querySelector("#friends-list").appendChild(noFriends);
      }
    } catch (error) {
      console.error("Error rendering friends list:", error);
      this.querySelector("#friends-list").innerHTML = "Error loading friends";
    }
  }
  createFriendElement(item) {
    const friendElement = document.createElement("div");
    friendElement.classList.add("contact");
    friendElement.setAttribute("id", item.uuid);
    friendElement.innerHTML = `
       <li>
          <img class="avatar" src="${item.friend.profile.avatar}" alt="avatar"/>  
          <span>${item.friend.username}</span>
          <br>
          <span>${item.uuid}</span>
        </li>
    `;
    return friendElement;
  }
}

customElements.define("friends-list", Friends);
export default Friends;
