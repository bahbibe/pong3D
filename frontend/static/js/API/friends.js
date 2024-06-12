class friends {
  constructor() {
  }
  async getFriends() {
    try {
      const response = await fetch("http://localhost:8000/api/friends/", {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`API request failed with status: ${response.status}`);
      }
      const res = await response.json();
      return res.data;
    } catch (error) {
      console.error("Error Loading friends:", error);
    }
  }
  async getDMs(id) {
    try {
      const response = await fetch(`http://localhost:8000/chat/${id}/`, {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });
      if (!response.ok) {
        console.log(response.status);
        throw new Error(`API request failed with status: ${response.status}`);
      }
      const res = await response.json();
      return res.messages;
    } catch (error) {
      console.error("Error Loading DMs:", error);
    }
  }
}
export { friends }