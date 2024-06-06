class LoginPage extends HTMLElement {
    
    constructor() {
        super()
    }

    connectedCallback() {

        const template = document.getElementById("login-page");
        const clone = template.content.cloneNode(true);
        this.appendChild(clone);
        const loginForm = this.querySelector("#login-form");
        loginForm.addEventListener("submit", this.handleSubmit);
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
        e.target.reset()
    }
}

window.customElements.define("login-page", LoginPage);

export { LoginPage }