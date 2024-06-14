class User {
  constructor() {}
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
export { User };