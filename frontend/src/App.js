import React, { useContext } from "react";
import { AuthProvider, AuthContext } from "./context/AuthContext";
import Login from "./pages/Login";
import Home from "./pages/Home";
import "./App.css";

const AppInner = () => {
  const { token } = useContext(AuthContext);
  return token ? <Home /> : <Login />;
};

const App = () => (
  <AuthProvider>
    <AppInner />
  </AuthProvider>
);

export default App;
