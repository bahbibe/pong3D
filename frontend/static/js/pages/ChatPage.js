

class ChatPage extends HTMLElement {
    
    constructor() {
        super()
    }

    connectedCallback() {

        const template = document.getElementById("chat-page");
        const clone = template.content.cloneNode(true);
        this.appendChild(clone);
        const chatForm = this.querySelector("#login-form");
        chatForm.addEventListener("submit", this.handleSubmit);
        const logOut = this.querySelector("#logout");
        const send = this.querySelector("#chat-send");
        send.addEventListener("click", this.handleSend);
        logOut.addEventListener("click", this.handleLogout);
    }

 
    async handleSubmit(e) {
        e.preventDefault()
        let username = e.target.username.value
        let password = e.target.password.value
        await fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            }),
            credentials: 'include'
        })
        const socket = new WebSocket('ws://localhost:8000/ws/chat/')

        socket.onmessage = (e) => {
            let data = JSON.parse(e.data)
            if (data.type === 'redirect') {
                alert("You are not logged in reedirecting to login page")
                window.location.href = `http://localhost:8000${data.url}`
            }

        }
        e.target.reset()
    }

    async handleLogout(e) {
        e.preventDefault()
        let response = await fetch('http://localhost:8000/api/auth/logout/', {
            method: 'POST',
            credentials: 'include'
        })
        let data = await response.json()
        console.log(data)
    }
}


window.customElements.define("chat-page", ChatPage);

export { ChatPage }