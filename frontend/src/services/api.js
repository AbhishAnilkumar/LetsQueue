import axios from "axios";

const api = axios.create({
  baseURL: "https://letsqueue-backend-s0g8.onrender.com/api/", 
});

let anonId = localStorage.getItem("anon_token");
if (!anonId) {
  anonId = crypto.randomUUID();
  localStorage.setItem("anon_token", anonId);
}

// Attach to every request
api.interceptors.request.use((config) => {
  config.headers["X-ANON-TOKEN"] = anonId;
  return config;
});

export default api;

