import { navigateTo } from "../router.js";
import { AbstractPage } from "./AbstarctPage.js";

class SearchPage extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.isFriend = false;
    this.container = document.querySelector("#search-container");
    this.checkFriend();
    // this.randerUser();
  }
  async checkFriend() {
    try {
      console.log("checkFriend");
      const response = await fetch('http://localhost:8000/api/friends/', { credentials: "include",});
      const data = await response.json();
      data.data.forEach((friend, _ , arr) => {
        console.log("friends",friend);
        if(friend.friend.username === window.SearchedUser)
        {
          console.log(`friend: ${friend.friend.username} === ${window.SearchedUser}`);
          this.isFriend = true;
          console.log(`isFriend 01: ${this.isFriend}`);
          return ;
        }
    })
    // const response1 = await fetch('http://localhost:8000/api/auth/users/', { credentials: "include",});
    //   const data1 = await response1.json();
    //   data1.data.forEach((user) => {
    //     console.log('userSer' , user);
    //     if (window.SearchedUser  && window.SearchedUser !== window.user.data.username &&  user.username === window.SearchedUser)
    //     {
    //       this.container.innerHTML = `
    //       <div class="secondary-bg box-sh-1 p-2 text-center rounded mx-auto mx-md-0" style="width: 160px; height: 140px;">
    //                 <div class="img ">
    //                   <img class="img-fluid rounded rounded-circle" src="${user.profile.avatar}" alt="" width="100" height="100">
    //                 </div>
    //                 <div class="my-2">
    //                   <a class="font-monospace fw-bold" href='/${this.isFriend ? "friend" : "user"}${user.id}'>${user.username} </a>
    //                 </div>
    //       </div>
    //       `
    //       console.log(`isFriend: ${this.isFriend}`);
    //       return;
    //     }
    // }) 
    this.randerUser();
    } catch (error) { console.log(error); }
  }

  async randerUser() {

    try {
      console.log(" randerUser");
      const response = await fetch('http://localhost:8000/api/auth/users/', { credentials: "include",});
      const data = await response.json();
      data.data.forEach((user) => {
        console.log('userSer' , user);
        if (window.SearchedUser  && window.SearchedUser !== window.user.data.username &&  user.username === window.SearchedUser)
        {
          this.container.innerHTML = `
          <div class="secondary-bg box-sh-1 p-2 text-center rounded mx-auto mx-md-0" style="width: 160px; height: 140px;">
                    <div class="img ">
                      <img class="img-fluid rounded rounded-circle" src="${user.profile.avatar}" alt="" width="100" height="100">
                    </div>
                    <div class="my-2">
                      <a class="font-monospace fw-bold" href='/${this.isFriend ? "friend" : "user"}${user.id}'>${user.username} </a>
                    </div>
          </div>
          `
          console.log(`isFriend: ${this.isFriend}`);
          return;
        }
      })

    } catch (error) { console.log(error); }

  }
}


class SearchBar extends AbstractPage {
  constructor() {
    super();
  }

  connectedCallback() {
    const template = document.getElementById("search-bar");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    this.form = this.querySelector("form#search");
    this.inputSearch = this.querySelector("[data-search]");

    this.form.addEventListener("submit", (e) => {
      e.preventDefault();
      window.SearchedUser = this.inputSearch.value;
      // console.log("====> SearchedUser: ", window.SearchedUser);
      this.inputSearch.value = "";
      navigateTo("/search");
    });
  }
}

window.customElements.define("search-bar", SearchBar);
window.customElements.define("search-page", SearchPage);

export { SearchPage , SearchBar}