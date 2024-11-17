import { API } from "../API/API.js";

class Profile extends HTMLElement {
  constructor() {
    super();
    this.API = new API();
  }
  connectedCallback() {
    const template = document.getElementById("profile");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.render();
  }
  async render() {
    try {
      const user = await this.API.getUser();
      this.querySelector("#profile-username").innerHTML = user.username;
      this.querySelector("#profile-avatar").src = user.profile.avatar;
    } catch (error) {
      console.error("Error rendering profile:", error);
    }
  }
}

customElements.define("profile-element", Profile);

export default Profile;
