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
      // for (let i = 0; i < dataBase.length; i++) {
      //   if (dataBase[i].id === uuid) {
      //     res.data.messages.push(dataBase[i]);
      //   }
      // }
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
  async getTournaments() {
    try {
      const response = await fetch("http://localhost:8000/game/get_tournaments", {
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

  async getTournament(tournament_id) {
    try {
      const response = await fetch(`http://localhost:8000/game/get_participants/${tournament_id}`, {
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
  async create_tournament() {
    try
    {
      const response = await fetch(`http://localhost:8000/game/create_tournament`,
        {
          method: "GET",
          headers: {
            "content-type": "application/json",
          },
          credentials: "include",
        }) ;
        if (!response.ok)
          throw new Error(`API request failed with status: ${response.status}`);
        const res = await response.json();
        return res.data;
    } catch (error)
    {
      console.error("Error creating tournament:", error);
    }
  }
}

export default API;
