class WebSockets {
    constructor() {
        // this.roomId = roomId || null;
        this.socket = new WebSocket(`ws://localhost:8000/ws/chat/`);
    }
    async connect() {

        this.socket.onopen = () => {
            console.log("connected")
        }
        this.socket.onerror = (error) => {
            console.log("error", error)
        }
        this.socket.onclose = () => {
            console.log("closed")
        }
    }
    async receive() {
        return new Promise((resolve, reject) => {
            this.socket.onmessage = (event) => {
                resolve(event.data);
                reject("Error receiving message");
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


export { WebSockets }