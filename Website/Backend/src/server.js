require("dotenv").config();

const fs = require("fs");
const express = require("express");
const path = require("path");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors()); // Enable CORS
app.use(express.json()); // Parse JSON request bodies
app.use(express.static(path.join(__dirname, "../../Frontend/src"))); // Serve static files

// Root endpoint
app.get("/", (req, res) => {
  res.send("KnoxDNS API is running...");
});

// Endpoint to fetch cache data
app.get("/api/cache", (req, res) => {
// app.get("http://localhost:8000/api/cache", (req, res) => {
  const cacheFilePath = path.join(__dirname, "../../Frontend/src/cache.json");
  console.log("dir path: ", __dirname);
  console.log("Cache file path: ", cacheFilePath);
  fs.readFile(cacheFilePath, "utf8", (err, data) => {
    if (err) {
      console.error("Error reading cache.json:", err);
      return res.status(500).json({ error: "Failed to read cache data" });
    }
    res.json(JSON.parse(data)); // Send JSON response
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});

