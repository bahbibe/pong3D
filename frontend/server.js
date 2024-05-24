import express from "express";
import path from "path";

const app = express();

const __dirname = path.dirname(new URL(import.meta.url).pathname);

app.use("/static", express.static(path.resolve(__dirname, "", "static")));

app.get("/*", (req, res) => {
  res.sendFile(path.resolve(__dirname, "", "index.html"));
});

app.listen(3000, () => {
  console.log("Server is running on http://localhost:3000");
});
