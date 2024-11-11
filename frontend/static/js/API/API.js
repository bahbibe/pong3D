
const dataBase = [{"id":"0ffececd-782e-426e-a64e-a61ecf2643eb","content":"erat curabitur gravida nisi","timestamp":"7:14 PM","read":false,"author_id":1,"conversation":"nisi"},
  {"id":"95b6631e-bde5-44d7-a42e-06986dc2a5ed","content":"lacinia","timestamp":"3:32 AM","read":true,"author_id":2,"conversation":"venenatis"},
  {"id":"4ea85a6f-52aa-43c1-bd0f-ae853b70e43d","content":"consequat","timestamp":"5:57 AM","read":true,"author_id":3,"conversation":"curae"},
]
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
      // console.log(dataBase);
      for (let i = 0; i < dataBase.length; i++) {
        if (dataBase[i].id === uuid) {
          res.data.messages.push(dataBase[i]);
        }
      }
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
