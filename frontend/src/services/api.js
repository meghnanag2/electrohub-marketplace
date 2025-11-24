import axios from "axios";

// Use relative URL; CRA dev server will proxy to backend
const api = axios.create({
  baseURL: "",
});

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

export default api;
