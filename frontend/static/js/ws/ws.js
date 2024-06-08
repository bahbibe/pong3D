class WebSockets {
    constructor() {
        this.socket = new WebSocket(`ws://localhost:8000/ws/chat/room_id/`);
    }
    showAlert(message) {
        // Get references to alert box elements (from previous example)
        const alertBox = document.getElementById('alert-box');
        const alertMessage = document.querySelector('.alert-message');
      
        // Update message content
        alertMessage.textContent = message;
      
        // Show alert box using existing logic
        alertBox.style.display = 'block';
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
                // alert("Unauthorized access. Please login.")
                showAlert("Unauthorized access. Please login.")
                window.location.href = "/login"
            }
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