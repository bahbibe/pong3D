class API {
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
      return res.data.messages;
    } catch (error) {
      console.error("Error Loading DMs:", error);
    }
  }
  async getUser() {
    try {
      const response = await fetch("http://localhost:8000/api/auth/me", {
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
      console.error("Error Loading profile:", error);
    }
  }
}
export default API;
