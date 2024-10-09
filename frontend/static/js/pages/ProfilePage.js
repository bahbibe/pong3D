import { navigateTo } from "../router.js";
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

    this.container = this.querySelector("#friend-container");
    // console.log(user);
    fullName.textContent = `${user.first_name} ${user.last_name}`;
    username.textContent =  `@${user.username}`;
    userImg.src = `${user.profile.avatar}`

    this.getFriend();

  }
  async getFriend(){
    try
    {
      const response = await fetch("http://localhost:8000/api/friends/", { credentials: "include"});
      const data = await response.json();
      if (response.ok)
      {
        const friends = data.data;
        console.log(friends);
        console.log(this.container);
        console.log();
        for (const friend of friends) {
          this.container.innerHTML += `
                    <div class="row p-1 rounded-1 justify-content-between align-items-center mb-2" style="background: linear-gradient(to right, rgb(20, 30, 48), rgb(36, 59, 85)); cursor: pointer;">
                      <div class="col-3 col-md-4">
                        <div class="d-flex align-items-center">
                        <img src="${friend.friend.profile.avatar}" class="img-fluid rounded-circle" width="35" alt="user profile image">
                          <div class="ps-2">
                            <a href="friend${friend.friend.id}"><span class="fw-bold text-capitalize" style="font-size: 14px;">${friend.friend.username}</span></a>
                          </div>
                        </div>
                      </div>
                      <div class="col-2 pe-2 ">
                        <span id="total"><strong>100</strong></span>
                      </div>
                      <div class="col-2 pe-2 ">
                        <span id="wins"><strong>100</strong></span>
                      </div>
                      <div class="col-2 pe-2 d-none d-md-block">
                        <span id="ratio"><strong>100</strong></span>
                      </div>
                      <div class="col-3 col-md-2 text-end">
                        <a href="#" role="button" class="bg-success font-glitch text-white text-decoration-none p-1">PLAY</a>
                      </div> 
                    </div>
                    `;
        }
      }

    }
    catch(e){ console.log(e);}
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
    this.notification = this.querySelector("div.content");
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
          <div class="notification">
                        <img src="${element.friend.profile.avatar}" alt="" />
                        <div class="text">
                            <p>
                                <a href="friend${element.friend.id}"><span class="name">${element.friend.username}</span> </a> has send a friend request
                            </p>
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