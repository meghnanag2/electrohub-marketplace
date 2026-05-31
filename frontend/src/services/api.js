import axios from "axios";

const api = axios.create({ baseURL: "" });

// Initialize token immediately from localStorage so first useEffect calls are authenticated
const _stored = localStorage.getItem("token");
if (_stored) api.defaults.headers.common["Authorization"] = `Bearer ${_stored}`;

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

export default api;
