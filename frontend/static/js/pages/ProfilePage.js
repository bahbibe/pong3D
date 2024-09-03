import { AbstractPage } from "./AbstarctPage.js";

class ProfilePage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("user-profile");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    const ctn = this.querySelector(".profile-content");
    const fullName = this.querySelector("#fullName");
    const username = this.querySelector("#username");
    const userImg = this.querySelector("#user-img"); 

    const user = window.user.data;
    fullName.textContent = `${user.first_name} ${user.last_name}`;
    username.textContent =  `${user.username}`;
    userImg.src = `${user.profile.avatar}`

  }
}

class mainNav extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("main-nav");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);

    const navUsername = this.querySelector("#nav-username");
    const navUserImg = this.querySelector("#nav-user-img");
    this.notification = this.querySelector(".notifications");
    this.notificationCounter = this.querySelector("[data-count]");
    const user = window.user.data;
    navUsername.textContent = `${user.username}`;
    navUserImg.src = `${user.profile.avatar}`

    const toggler = this.querySelector(".toggler-btn");
    toggler.addEventListener("click", function () {
    document.querySelector("#sidebar").classList.toggle("collapsed");
  });
  this.RequestFrirends();

  }
  RequestFrirends() {
    fetch("http://localhost:8000/api/friends/requests/", {
      method: "GET",
      credentials: "include",
    })
      .then((response) => response.json())
      .then((data) => {
        const friends = data.data;
        this.notificationCounter.textContent = friends.length;
        friends.forEach(element => {
          console.log();
          this.notification.innerHTML += `
          <div class="info d-flex justify-content-between mb-2">
              <div class="info__title">
              <img src="${element.friend.profile.avatar}" class="rounded rounded-2" height="40" alt="friend image" loading="lazy"/>
                <span id="">${element.friend.username}</span>
              </div>
              <div class="info__close d-flex">
                <a><i class="fa-solid fa-xmark me-2"></i></a> 
                <a><i class="fa-solid fa-check"></i></a>
              </div>
          </div>
          `
          
        });
      }).catch((error) => {
        console.log(error);
      });
  }
}

window.customElements.define("user-profile", ProfilePage);
window.customElements.define("main-nav", mainNav);

export { ProfilePage }