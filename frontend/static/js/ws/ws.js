class WebSock {
    constructor(id) {
        this.socket = new WebSocket(`ws://localhost:8000/ws/chat/${id}/`);
    }

    async connect() {
        this.socket.onopen = () => {
            console.log("ws connected")
        }
        this.socket.onerror = (error) => {
            console.log("error", error)
        }
        this.socket.onclose = (event) => {
            console.log("ws closed")
            if (event.code === 4001) {
                alert("Unauthorized access. Please login.")
                window.location.href = "/login"
            }
        }
    }
    async receive() {
        return new Promise((resolve, reject) => {
            this.socket.onmessage = (event) => {
                resolve(event.data);
            }
            this.socket.onerror = (error) => {
                reject(error);
            }
        });
    }
    async send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.error("WebSocket is not open. ReadyState:", this.socket ? this.socket.readyState : "Socket is null");
        }
    }
    async close() {
        if (this.socket) {
            this.socket.close();
        } else {
            console.error("WebSocket is not initialized.");
        }
    }
}

export { WebSock }