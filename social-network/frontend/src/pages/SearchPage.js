import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api, avatarUrl, userInitials } from "../api";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [users, setUsers] = useState(null); // null = поиск ещё не выполнялся
  const [loading, setLoading] = useState(false);

  const search = async () => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      setUsers(await api.searchUsers(q));
    } catch {
      setUsers([]);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setQ(e.target.value);
    // Сбрасываем результаты при изменении запроса
    if (users !== null) setUsers(null);
  };

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 20 }}>Поиск пользователей</h1>
      <div className="search-row">
        <input
          className="form-input"
          value={q}
          onChange={handleChange}
          placeholder="Введите имя или email"
          onKeyDown={(e) => e.key === "Enter" && search()}
        />
        <button onClick={search} className="btn btn-primary" disabled={loading}>
          {loading ? "Поиск..." : "Найти"}
        </button>
      </div>

      {users !== null && users.map((u) => (
        <Link key={u.id} to={`/user/${u.id}`} className="user-card">
          <div className="avatar">
            {avatarUrl(u) ? <img src={avatarUrl(u)} alt="" /> : userInitials(u)}
          </div>
          <div className="user-card-info">
            <b>{u.username}</b>
            {u.bio && <p>{u.bio}</p>}
          </div>
        </Link>
      ))}

      {users !== null && users.length === 0 && (
        <div className="empty-state"><p>Ничего не найдено</p></div>
      )}
    </div>
  );
}
