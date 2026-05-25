import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import { api } from "./api";
import RegisterPage from "./pages/RegisterPage";
import LoginPage from "./pages/LoginPage";
import FeedPage from "./pages/FeedPage";
import MyPostsPage from "./pages/MyPostsPage";
import FollowingPage from "./pages/FollowingPage";
import ProfilePage from "./pages/ProfilePage";
import UserPage from "./pages/UserPage";
import SearchPage from "./pages/SearchPage";
import CreatePostPage from "./pages/CreatePostPage";

function Navbar() {
  const nav = useNavigate();
  const loggedIn = api.isLoggedIn();
  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">SocialNet</Link>
      {loggedIn ? (
        <>
          <Link to="/feed" className="navbar-link">Лента</Link>
          <Link to="/my-posts" className="navbar-link">Мои посты</Link>
          <Link to="/following" className="navbar-link">Подписки</Link>
          <Link to="/search" className="navbar-link">Поиск</Link>
          <Link to="/profile" className="navbar-link">Профиль</Link>
          <button className="navbar-logout" onClick={() => { api.logout(); nav("/login"); }}>Выйти</button>
        </>
      ) : (
        <>
          <Link to="/login" className="navbar-link">Вход</Link>
          <Link to="/register" className="navbar-link">Регистрация</Link>
        </>
      )}
    </nav>
  );
}

function ProtectedRoute({ children }) {
  return api.isLoggedIn() ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <div className="container">
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/feed" element={<ProtectedRoute><FeedPage /></ProtectedRoute>} />
          <Route path="/my-posts" element={<ProtectedRoute><MyPostsPage /></ProtectedRoute>} />
          <Route path="/following" element={<ProtectedRoute><FollowingPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/user/:id" element={<ProtectedRoute><UserPage /></ProtectedRoute>} />
          <Route path="/search" element={<ProtectedRoute><SearchPage /></ProtectedRoute>} />
          <Route path="/create-post" element={<ProtectedRoute><CreatePostPage /></ProtectedRoute>} />
          <Route path="/edit-post/:id" element={<ProtectedRoute><CreatePostPage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/feed" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
