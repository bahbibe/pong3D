class HomePage extends HTMLElement {
  constructor() {
    super()
  }

  connectedCallback() {
    const template = document.getElementById("home-page");
    const clone = template.content.cloneNode(true);
    this.appendChild(clone);
    // fetch("http://localhost:8000/api/auth/login/", {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json",
    //   },
    //   body: JSON.stringify({
    //     username: "test",
    //     password: "test123",
    //   }),
    // })
    //   .then((response) => response.json())
    //   .then((data) => {
    //     console.log(data);
    //     const d = new Date();
    //     d.setTime(d.getTime() + (1 * 24 * 60 * 60 * 1000));
    //     let expires = "expires=" + d.toUTCString();
    //     document.cookie = "accesstoken" + "=" + data.access_token + ";" + expires + ";path=/";
    //   })
    // console.log("Home Page Connected");
    // fetch("http://localhost:8000/api/auth/me/", {
    //   method: "GET",
    //   headers: {
    //     "Content-Type": "application/json",
    //   },
    //   credentials: "include",
    // }).then((response) => response.json())
    //   .then((data) => {
    //     console.log("User: ", data);
    //   });

    // try {
    //   const websocket = new WebSocket("ws://localhost:8000/ws/chat/");
    //   websocket.onopen = () => {
    //     console.log("Connected to the websocket server");
    //   };
    //   websocket.onbeforeopen = function () {
    //     const jwtToken = document.cookie.split('; ').find(row => row.startsWith('accesstoken')).split('=')[1];
    //     websocket.setRequestHeader('Authorization', `Bearer ${jwtToken}`);
    //   };
    //   }
    // catch (error) {
    //   console.error("Error: ", error);
    // }
  }
}

window.customElements.define("home-page", HomePage);

export { HomePage }