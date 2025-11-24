import React, { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

const Home = () => {
  const { logout } = useContext(AuthContext);

  return (
    <div className="home-page">
      <header className="navbar">
        <h2>ElectroHub Marketplace</h2>
        <button onClick={logout}>Logout</button>
      </header>

      <main className="feed">
        <h3>Recommended Listings</h3>
        <p>Later we will show real items here from the backend.</p>
      </main>
    </div>
  );
};

export default Home;
