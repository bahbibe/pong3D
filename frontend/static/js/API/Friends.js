class Friendships {
  constructor() {}
  async getFriends() {
    try {
      const response = await fetch("http://localhost:8000/api/friends/", {
        method: "GET",
        headers: {
          "content-type": "application/json",
        },
        credentials: "include",
      });
      if (!response.ok)
        throw new Error(`API request failed with status: ${response.status}`);
      const res = await response.json();
      return res.data;
    } catch (error) {
      console.error("Error Loading friends:", error);
    }
  }
  async getMessages(uuid) {
    try {
      console.log("uuid", uuid);  // Debugging
      const response = await fetch(`http://localhost:8000/chat/${uuid}/`, {
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
      console.log("res", res);  // Debugging
      return res.data.messages;
    } catch (error) {
      console.error("Error Loading DMs:", error);
    }
  }
}
export { Friendships };
